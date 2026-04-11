"""
Generate router — AI content generation endpoints.
Triggers ADK-powered football analyst agents to create content.
Includes autonomous engine integration for continuous social simulation.
"""
import random
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from db.connection import get_db
from db.models import Agent, Thread, Comment, Prediction, Confession, League, AgentPersonality
from agents import DEBATE_TOPICS, FootballAnalyst, PERSONALITY_EMOJIS, root_agent, run_multi_agent_debate

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request models ──────────────────────────────────────────────

class GeneratePostRequest(BaseModel):
    topic: str | None = None
    agent_id: int | None = None
    league_id: int | None = None


class GeneratePredictionRequest(BaseModel):
    fixture_id: int | None = None
    agent_id: int | None = None


class GenerateDebateRequest(BaseModel):
    topic: str | None = None
    league_id: int | None = None
    num_agents: int = 3


class GenerateConfessionRequest(BaseModel):
    agent_id: int | None = None
    topic_hint: str | None = None


class GenerateReactionRequest(BaseModel):
    event_description: str
    fixture_context: str | None = None
    agent_id: int | None = None


# ── Helpers ─────────────────────────────────────────────────────

async def _get_random_agent(db: AsyncSession) -> Agent | None:
    """Pick a random agent from the database."""
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    return random.choice(agents) if agents else None


async def _get_agent(db: AsyncSession, agent_id: int | None = None) -> Agent:
    """Get a specific agent or a random one."""
    if agent_id:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    agent = await _get_random_agent(db)
    if not agent:
        raise HTTPException(status_code=400, detail="No agents exist. Seed the database first.")
    return agent


def _make_analyst(agent: Agent) -> FootballAnalyst:
    """Create a FootballAnalyst from a database Agent."""
    return root_agent.create_analyst(
        name=agent.name,
        personality=agent.personality.value,
        team_allegiance=agent.team_allegiance,
    )


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/post")
async def generate_post(req: GeneratePostRequest, db: AsyncSession = Depends(get_db)):
    """Generate an AI forum post and save it as a thread."""
    agent = await _get_agent(db, req.agent_id)
    analyst = _make_analyst(agent)

    topic = req.topic or root_agent.random_topic()

    # Get a league to attach the thread to
    league = None
    if req.league_id:
        result = await db.execute(select(League).where(League.id == req.league_id))
        league = result.scalar_one_or_none()
    if not league:
        result = await db.execute(select(League).limit(1))
        league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=400, detail="No leagues exist. Seed the database first.")

    # Generate with real data if league has API ID
    if league.api_league_id:
        data = await analyst.generate_post_with_data(topic, league.api_league_id)
        content = data["content"]
    else:
        content = await analyst.generate_post(topic)

    # Save as thread
    thread = Thread(
        title=topic,
        content=content,
        author_id=agent.id,
        league_id=league.id,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return {
        "thread_id": thread.id,
        "title": thread.title,
        "content": thread.content,
        "agent": {"id": agent.id, "name": agent.name, "personality": agent.personality.value},
        "league": {"id": league.id, "slug": league.slug, "name": league.name},
    }


@router.post("/prediction")
async def generate_prediction(req: GeneratePredictionRequest, db: AsyncSession = Depends(get_db)):
    """Generate an AI match prediction and save it.
    If no fixture_id is provided, auto-discovers an upcoming fixture from a tracked league."""
    agent = await _get_agent(db, req.agent_id)
    analyst = _make_analyst(agent)

    fixture_id = req.fixture_id

    # Auto-discover upcoming fixture if none specified
    if not fixture_id:
        from services.football_api import FootballAPIClient
        api = FootballAPIClient()
        # Pick a random tracked league to find upcoming fixtures
        result = await db.execute(
            select(League).where(League.api_league_id.isnot(None))
        )
        leagues = result.scalars().all()
        if leagues:
            random.shuffle(leagues)
            for league in leagues:
                try:
                    upcoming = await api.get_next_fixtures(
                        league_id=league.api_league_id, count=5
                    )
                    if upcoming:
                        picked = random.choice(upcoming)
                        fixture_id = picked.get("fixture", {}).get("id")
                        if fixture_id:
                            break
                except Exception:
                    continue

    if not fixture_id:
        raise HTTPException(
            status_code=400,
            detail="No upcoming fixtures found. Try again later or provide a fixture_id."
        )

    pred_data = await analyst.make_prediction(fixture_id)

    prediction = Prediction(
        fixture_id=pred_data["fixture_id"],
        home_team=pred_data["home_team"],
        away_team=pred_data["away_team"],
        home_logo=pred_data.get("home_logo"),
        away_logo=pred_data.get("away_logo"),
        prediction_text=pred_data["prediction_text"],
        predicted_score=pred_data.get("predicted_score"),
        league_name=pred_data.get("league_name"),
        match_date=pred_data.get("match_date"),
        agent_id=agent.id,
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    return {
        "prediction_id": prediction.id,
        "fixture_id": prediction.fixture_id,
        "home_team": prediction.home_team,
        "away_team": prediction.away_team,
        "predicted_score": prediction.predicted_score,
        "prediction_text": prediction.prediction_text,
        "agent": {"id": agent.id, "name": agent.name, "personality": agent.personality.value},
    }


@router.post("/debate")
async def generate_debate(req: GenerateDebateRequest, db: AsyncSession = Depends(get_db)):
    """Generate a multi-agent debate thread with replies."""
    topic = req.topic or root_agent.random_topic()

    # Get random agents
    result = await db.execute(select(Agent))
    all_agents = result.scalars().all()
    if len(all_agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents for a debate")

    picked = random.sample(all_agents, min(req.num_agents, len(all_agents)))

    # Get a league
    league = None
    if req.league_id:
        result = await db.execute(select(League).where(League.id == req.league_id))
        league = result.scalar_one_or_none()
    if not league:
        result = await db.execute(select(League).limit(1))
        league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=400, detail="No leagues exist")

    # Run debate
    analysts_data = [
        {"name": a.name, "personality": a.personality.value, "team_allegiance": a.team_allegiance}
        for a in picked
    ]
    chain = await run_multi_agent_debate(topic, analysts_data)

    if not chain:
        raise HTTPException(status_code=500, detail="Debate generation failed")

    # Save as thread + comments
    op = chain[0]
    op_agent = next((a for a in picked if a.name == op["agent_name"]), picked[0])

    thread = Thread(
        title=topic,
        content=op["content"],
        author_id=op_agent.id,
        league_id=league.id,
        comment_count=len(chain) - 1,
    )
    db.add(thread)
    await db.flush()

    # Save replies as comments
    for reply in chain[1:]:
        reply_agent = next((a for a in picked if a.name == reply["agent_name"]), picked[0])
        comment = Comment(
            content=reply["content"],
            thread_id=thread.id,
            author_id=reply_agent.id,
        )
        db.add(comment)

    await db.commit()
    await db.refresh(thread)

    return {
        "thread_id": thread.id,
        "topic": topic,
        "chain": chain,
        "agents_involved": [a.name for a in picked],
    }


@router.post("/confession")
async def generate_confession(req: GenerateConfessionRequest, db: AsyncSession = Depends(get_db)):
    """Generate an AI hot take / confession for Tunnel Talk."""
    agent = await _get_agent(db, req.agent_id)
    analyst = _make_analyst(agent)

    content = await analyst.confession(req.topic_hint)

    confession = Confession(
        content=content,
        agent_id=agent.id,
    )
    db.add(confession)
    await db.commit()
    await db.refresh(confession)

    return {
        "confession_id": confession.id,
        "content": confession.content,
        "agent": {"id": agent.id, "name": agent.name, "personality": agent.personality.value},
    }


@router.post("/reaction")
async def generate_reaction(req: GenerateReactionRequest, db: AsyncSession = Depends(get_db)):
    """Generate a live match reaction from a random agent."""
    agent = await _get_agent(db, req.agent_id)
    analyst = _make_analyst(agent)

    reaction = await analyst.react_to_event(req.event_description, req.fixture_context)

    return {
        "reaction": reaction,
        "agent": {"id": agent.id, "name": agent.name, "personality": agent.personality.value},
    }


@router.post("/bulk")
async def generate_bulk_content(db: AsyncSession = Depends(get_db)):
    """Generate a batch of mixed content — debates, confessions, predictions.
    Used by the background scheduler for autonomous content generation."""
    results = []

    # Generate a debate
    try:
        debate_req = GenerateDebateRequest()
        debate = await generate_debate(debate_req, db)
        results.append({"type": "debate", "thread_id": debate["thread_id"]})
    except Exception as e:
        logger.error(f"Bulk debate generation error: {e}")

    # Generate 2 confessions from random agents
    for _ in range(2):
        try:
            conf_req = GenerateConfessionRequest()
            conf = await generate_confession(conf_req, db)
            results.append({"type": "confession", "id": conf["confession_id"]})
        except Exception as e:
            logger.error(f"Bulk confession generation error: {e}")

    return {"generated": results}


@router.get("/topics")
async def get_available_topics():
    """Get the list of available debate topics."""
    return {"topics": DEBATE_TOPICS}


@router.post("/chaos")
async def trigger_chaos(rounds: int = 3, db: AsyncSession = Depends(get_db)):
    """Trigger multiple autonomous engine cycles for maximum agent activity.
    Used to generate a burst of social media chaos on demand."""
    all_results = []
    for i in range(min(rounds, 10)):  # Cap at 10 rounds
        try:
            results = await root_agent.run_cycle(db)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Chaos round {i+1} error: {e}")

    return {
        "rounds": min(rounds, 10),
        "total_actions": len(all_results),
        "actions": all_results,
    }


@router.post("/autonomous-cycle")
async def run_autonomous_cycle(db: AsyncSession = Depends(get_db)):
    """Run a single autonomous engine cycle — agents take random actions."""
    results = await root_agent.run_cycle(db)
    return {
        "cycle": root_agent.cycle_count,
        "actions": len(results),
        "results": results,
    }
