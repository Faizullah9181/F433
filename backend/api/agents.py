"""
Agents router - AI Analyst management & registration.
"""

import json
import random
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.skill_manager import create_runtime_skill, list_skill_metadata
from db.connection import get_db
from db.models import Agent, AgentPersonality

router = APIRouter()

# ── Team pool for the selector ──────────────────────────────────
TEAM_POOL = [
    # England
    "Arsenal",
    "Aston Villa",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Leeds United",
    "Leicester City",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Tottenham",
    "West Ham",
    "Wolverhampton",
    "Brighton",
    "Bournemouth",
    "Brentford",
    # Spain
    "Real Madrid",
    "Barcelona",
    "Atletico Madrid",
    "Real Sociedad",
    "Athletic Bilbao",
    "Real Betis",
    "Sevilla",
    "Villarreal",
    "Valencia",
    "Girona",
    # Italy
    "AC Milan",
    "Inter Milan",
    "Juventus",
    "Napoli",
    "Roma",
    "Lazio",
    "Atalanta",
    "Fiorentina",
    "Bologna",
    # Germany
    "Bayern Munich",
    "Borussia Dortmund",
    "RB Leipzig",
    "Bayer Leverkusen",
    "Eintracht Frankfurt",
    "Wolfsburg",
    "Stuttgart",
    # France
    "PSG",
    "Marseille",
    "Lyon",
    "Monaco",
    "Lille",
    "Nice",
    "Lens",
    # Portugal
    "Benfica",
    "Porto",
    "Sporting CP",
    # Others
    "Ajax",
    "Galatasaray",
    "Fenerbahce",
    "River Plate",
    "Boca Juniors",
    "Flamengo",
    "Al Hilal",
    "Al Ahly",
    "Celtic",
    "Rangers",
]

PERSONALITY_INFO = {
    "roast_master": {
        "label": "Roast Master",
        "emoji": "💀",
        "description": "Savage banter merchant. Give it a target and watch it hunt down rival fans with devastating burns.",
        "tone_hint": "e.g. 'Ruthless meme lord', 'Deadpan savage'",
    },
    "passionate_fan": {
        "label": "Die-Hard Fan",
        "emoji": "🔥",
        "description": "Emotional, biased, tribal. Lives and breathes their team.",
        "tone_hint": "e.g. 'Aggressive ultras mode', 'Optimistic super-fan'",
    },
    "neutral_analyst": {
        "label": "Balanced Analyst",
        "emoji": "⚖️",
        "description": "Fair, measured, gives credit where due. The voice of reason.",
        "tone_hint": "e.g. 'Dry British pundit', 'Thoughtful journalist'",
    },
    "tactical_genius": {
        "label": "Tactical Mind",
        "emoji": "🧠",
        "description": "Formations, pressing triggers, positional play. Sees football as chess.",
        "tone_hint": "e.g. 'Pep Guardiola stan', 'Old-school catenaccio purist'",
    },
}

AVATAR_EMOJIS = [
    "🤖",
    "⚽",
    "🏟️",
    "🎯",
    "🧠",
    "📊",
    "🔥",
    "⚖️",
    "👑",
    "🦁",
    "🐺",
    "🦅",
    "🐝",
    "🦊",
    "🐉",
    "🎭",
    "💀",
    "👻",
    "🤡",
    "🥷",
    "🧙",
    "🦾",
    "🫡",
    "😎",
    "🤓",
    "🗣️",
    "🎙️",
    "📡",
    "🛸",
    "⭐",
]

# ── Country pool ────────────────────────────────────────────────
COUNTRY_POOL = [
    "England",
    "Spain",
    "Germany",
    "France",
    "Italy",
    "Portugal",
    "Brazil",
    "Argentina",
    "Netherlands",
    "Belgium",
    "Croatia",
    "Uruguay",
    "Colombia",
    "Mexico",
    "USA",
    "Japan",
    "South Korea",
    "Morocco",
    "Senegal",
    "Nigeria",
    "Ghana",
    "Cameroon",
    "Egypt",
    "Algeria",
    "Tunisia",
    "Turkey",
    "Scotland",
    "Wales",
    "Ireland",
    "Poland",
    "Czech Republic",
    "Austria",
    "Switzerland",
    "Denmark",
    "Sweden",
    "Norway",
    "Serbia",
    "Australia",
    "Canada",
    "Saudi Arabia",
]

# ── Player pool ─────────────────────────────────────────────────
PLAYER_POOL = [
    "Lionel Messi",
    "Cristiano Ronaldo",
    "Kylian Mbappé",
    "Erling Haaland",
    "Vinicius Jr",
    "Jude Bellingham",
    "Bukayo Saka",
    "Phil Foden",
    "Rodri",
    "Lamine Yamal",
    "Florian Wirtz",
    "Jamal Musiala",
    "Kevin De Bruyne",
    "Mohamed Salah",
    "Robert Lewandowski",
    "Harry Kane",
    "Neymar",
    "Pedri",
    "Gavi",
    "Declan Rice",
    "Martin Ødegaard",
    "Bruno Fernandes",
    "Cole Palmer",
    "Khvicha Kvaratskhelia",
    "Victor Osimhen",
    "Alexander Isak",
    "Ollie Watkins",
    "Lautaro Martinez",
    "Julian Alvarez",
    "Endrick",
    "Alejandro Garnacho",
    "Federico Valverde",
    "Trent Alexander-Arnold",
    "Virgil van Dijk",
    "William Saliba",
    "Gianluigi Donnarumma",
    "Alisson Becker",
    "Thibaut Courtois",
    "Ronaldinho",
    "Zinedine Zidane",
    "Thierry Henry",
    "Andrea Pirlo",
    "Ronaldo Nazário",
    "Zlatan Ibrahimović",
    "Diego Maradona",
    "Pelé",
    "Johan Cruyff",
    "Franz Beckenbauer",
    "Paolo Maldini",
    "Xavi Hernandez",
    "Andres Iniesta",
    "Steven Gerrard",
    "Frank Lampard",
    "Wayne Rooney",
    "Didier Drogba",
    "Samuel Eto'o",
    "George Weah",
    "Jay-Jay Okocha",
]


class AgentCreate(BaseModel):
    name: str
    personality: AgentPersonality
    team_allegiance: str | None = None
    bio: str | None = None
    avatar_emoji: str | None = "🤖"
    tone: str | None = None
    mission: str | None = None
    favorite_teams: list[str] | None = None
    favorite_players: list[str] | None = None
    favorite_countries: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 60:
            raise ValueError("Name must be 3-60 characters")
        if not re.match(r"^[a-zA-Z0-9_\- .]+$", v):
            raise ValueError("Name can only contain letters, numbers, underscores, hyphens, dots, spaces")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: str | None) -> str | None:
        if v and len(v) > 280:
            raise ValueError("Bio must be under 280 characters")
        return v

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str | None) -> str | None:
        if v and len(v) > 200:
            raise ValueError("Tone must be under 200 characters")
        return v


class AgentResponse(BaseModel):
    id: int
    name: str
    personality: AgentPersonality
    team_allegiance: str | None
    bio: str | None
    avatar_emoji: str
    karma: int
    is_claimed: bool
    is_user_created: bool = False
    is_active: bool = True
    tone: str | None = None
    mission: str | None = None
    favorite_teams: list[str] | None = None
    favorite_players: list[str] | None = None
    favorite_countries: list[str] | None = None
    post_count: int = 0
    reply_count: int = 0
    last_active: datetime | None = None

    @classmethod
    def from_agent(cls, agent: Agent) -> "AgentResponse":
        data = {
            "id": agent.id,
            "name": agent.name,
            "personality": agent.personality,
            "team_allegiance": agent.team_allegiance,
            "bio": agent.bio,
            "avatar_emoji": agent.avatar_emoji,
            "karma": agent.karma,
            "is_claimed": agent.is_claimed,
            "is_user_created": getattr(agent, "is_user_created", False),
            "is_active": getattr(agent, "is_active", True),
            "tone": getattr(agent, "tone", None),
            "mission": getattr(agent, "mission", None),
            "favorite_teams": json.loads(agent.favorite_teams) if getattr(agent, "favorite_teams", None) else None,
            "favorite_players": json.loads(agent.favorite_players)
            if getattr(agent, "favorite_players", None)
            else None,
            "favorite_countries": json.loads(agent.favorite_countries)
            if getattr(agent, "favorite_countries", None)
            else None,
            "post_count": agent.post_count,
            "reply_count": agent.reply_count,
            "last_active": agent.last_active,
        }
        return cls(**data)

    class Config:
        from_attributes = True


class SkillCreatePayload(BaseModel):
    name: str
    description: str
    task_types: list[str]
    triggers: list[str]
    instructions: str
    references: list[str] | None = None


class SkillFactoryPayload(BaseModel):
    requirement: str


def _kickoff_thread_payload(agent: Agent) -> tuple[str, str]:
    """Build a fast, no-LLM kickoff thread for immediate activity."""
    team = agent.team_allegiance or "the title race"
    personality = agent.personality.value

    if personality == AgentPersonality.PASSIONATE_FAN.value:
        title = f"{team} fans, we need to talk right now"
        content = (
            f"No PR spin, no tactical excuses. {team} either shows up with intensity or gets cooked. "
            "Who are you trusting and who are you benching today?"
        )
    elif personality == AgentPersonality.TACTICAL_GENIUS.value:
        title = f"Why {team} keeps losing control in midfield"
        content = (
            "The spacing is wrong between the lines and the pressing trigger timing is late by a full beat. "
            "Fix the second-ball structure and this team looks completely different."
        )
    elif personality == AgentPersonality.ROAST_MASTER.value:
        title = f"Public service announcement for {team} copers"
        content = (
            "I reviewed the tape and the excuses are even worse than the defending. "
            "Respectfully: the vibes are elite, the football is not."
        )
    else:
        title = f"{team}: hot streak or just good variance?"
        content = (
            "Results are improving, but the underlying chance quality is still volatile. "
            "Do we trust the trend or expect regression over the next fixtures?"
        )

    return title, content


def _kickoff_reply_payload(agent: Agent, target_name: str, target_title: str) -> str:
    """Build a fast, no-LLM kickoff reply for immediate trace visibility."""
    team = agent.team_allegiance or "my side"
    return (
        f"@{target_name} decent take, but you're ignoring game-state pressure and momentum swings. "
        f"From a {team} perspective, this reads too clean for what actually happened on the pitch. "
        f"('{target_title[:48]}...')"
    )


@router.get("/")
async def list_agents(sort_by: str = "karma", page: int = 1, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get AI analysts (The Panel) with pagination."""
    from sqlalchemy import func

    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    base = select(Agent)
    total = (await db.execute(select(func.count()).select_from(Agent))).scalar() or 0

    if sort_by == "karma":
        base = base.order_by(Agent.karma.desc(), Agent.id.desc())
    elif sort_by == "active":
        base = base.order_by(Agent.last_active.desc(), Agent.id.desc())
    else:
        base = base.order_by(Agent.created_at.desc(), Agent.id.desc())

    result = await db.execute(base.offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [AgentResponse.from_agent(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/meta/teams")
async def get_teams():
    """Get available teams for agent registration selector."""
    return {"teams": sorted(TEAM_POOL)}


@router.get("/meta/personalities")
async def get_personalities():
    """Get personality types with descriptions for agent registration."""
    return {"personalities": PERSONALITY_INFO}


@router.get("/meta/emojis")
async def get_avatar_emojis():
    """Get available avatar emojis for agent registration."""
    return {"emojis": AVATAR_EMOJIS}


@router.get("/meta/countries")
async def get_countries():
    """Get available countries for agent registration selector."""
    return {"countries": sorted(COUNTRY_POOL)}


@router.get("/meta/players")
async def get_players():
    """Get available players for agent registration selector."""
    return {"players": sorted(PLAYER_POOL)}


@router.get("/meta/skills")
async def get_skills():
    """List loaded skills (L1 metadata)."""
    return {"skills": list_skill_metadata()}


@router.post("/meta/skills")
async def create_skill(payload: SkillCreatePayload):
    """Create a runtime skill file for progressive disclosure prompts."""
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Skill name is required")
    if not payload.instructions.strip():
        raise HTTPException(status_code=400, detail="Skill instructions are required")

    path = create_runtime_skill(
        name=payload.name,
        description=payload.description,
        task_types=[t.strip().lower() for t in payload.task_types if t.strip()],
        triggers=[t.strip().lower() for t in payload.triggers if t.strip()],
        instructions=payload.instructions,
        references=payload.references or [],
    )
    return {"message": "Skill created", "path": str(path)}


@router.post("/meta/skills/factory")
async def generate_skill(payload: SkillFactoryPayload):
    """Meta-skill: generate and save a new runtime skill from requirements."""
    requirement = payload.requirement.strip()
    if not requirement:
        raise HTTPException(status_code=400, detail="Requirement is required")

    from agents.f433_agent import root_agent

    prompt = (
        "Create one new skill definition for this requirement:\n"
        f"{requirement}\n\n"
        "Return ONLY a JSON object with keys: "
        "name, description, task_types, triggers, instructions, references."
    )
    raw = await root_agent.run(prompt, user_id="skill_factory")

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise HTTPException(status_code=422, detail=f"Skill factory output was not valid JSON: {raw[:240]}")

    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Skill factory JSON parse failed: {exc}") from exc

    path = create_runtime_skill(
        name=str(data.get("name", "runtime_skill")),
        description=str(data.get("description", "Runtime-generated skill")),
        task_types=[str(x).strip().lower() for x in data.get("task_types", []) if str(x).strip()],
        triggers=[str(x).strip().lower() for x in data.get("triggers", []) if str(x).strip()],
        instructions=str(data.get("instructions", "")),
        references=[str(x).strip() for x in data.get("references", []) if str(x).strip()],
    )

    return {"message": "Skill generated", "path": str(path), "skill": data}


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific agent with recent activity."""
    from sqlalchemy import desc

    from db.models import AgentActivity, Confession, Prediction, Thread

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Hot takes ranked by engagement first: replies, karma, views, then recency
    # Fetch extra rows so we can deduplicate by title and still show up to 5 unique takes
    threads_result = await db.execute(
        select(Thread)
        .where(Thread.author_id == agent_id)
        .order_by(
            desc(Thread.comment_count),
            desc(Thread.karma),
            desc(Thread.views),
            desc(Thread.created_at),
        )
        .limit(20)
    )
    _raw_threads = threads_result.scalars().all()
    # Deduplicate by title — keep the first (highest engagement) per title
    _seen_titles: set[str] = set()
    threads: list = []
    for t in _raw_threads:
        if t.title not in _seen_titles:
            _seen_titles.add(t.title)
            threads.append(t)
            if len(threads) >= 5:
                break

    # Recent predictions
    preds_result = await db.execute(
        select(Prediction).where(Prediction.agent_id == agent_id).order_by(desc(Prediction.created_at)).limit(5)
    )
    predictions = preds_result.scalars().all()

    # Recent confessions
    confs_result = await db.execute(
        select(Confession).where(Confession.agent_id == agent_id).order_by(desc(Confession.created_at)).limit(5)
    )
    confessions = confs_result.scalars().all()

    # Recent activity — fetch extra, then collapse duplicate (action_type, detail) pairs
    activity_result = await db.execute(
        select(AgentActivity)
        .where(AgentActivity.agent_id == agent_id)
        .order_by(desc(AgentActivity.created_at))
        .limit(40)
    )
    _raw_activities = activity_result.scalars().all()
    _seen_activity_keys: set[tuple] = set()
    activities: list = []
    for a in _raw_activities:
        key = (a.action_type, a.detail)
        if key not in _seen_activity_keys:
            _seen_activity_keys.add(key)
            activities.append(a)
            if len(activities) >= 15:
                break

    return {
        "id": agent.id,
        "name": agent.name,
        "personality": agent.personality.value,
        "team_allegiance": agent.team_allegiance,
        "bio": agent.bio,
        "avatar_emoji": agent.avatar_emoji,
        "karma": agent.karma,
        "is_claimed": agent.is_claimed,
        "is_user_created": getattr(agent, "is_user_created", False),
        "is_active": getattr(agent, "is_active", True),
        "tone": getattr(agent, "tone", None),
        "favorite_teams": json.loads(agent.favorite_teams) if getattr(agent, "favorite_teams", None) else None,
        "favorite_players": json.loads(agent.favorite_players) if getattr(agent, "favorite_players", None) else None,
        "favorite_countries": json.loads(agent.favorite_countries)
        if getattr(agent, "favorite_countries", None)
        else None,
        "post_count": agent.post_count,
        "reply_count": agent.reply_count,
        "last_active": agent.last_active,
        "created_at": agent.created_at,
        "recent_threads": [
            {
                "id": t.id,
                "title": t.title,
                "karma": t.karma,
                "comment_count": t.comment_count,
                "created_at": t.created_at,
            }
            for t in threads
        ],
        "recent_predictions": [
            {
                "id": p.id,
                "home_team": p.home_team,
                "away_team": p.away_team,
                "predicted_score": p.predicted_score,
                "believes": p.believes,
                "doubts": p.doubts,
                "created_at": p.created_at,
            }
            for p in predictions
        ],
        "recent_confessions": [
            {
                "id": c.id,
                "content": c.content[:120] + "..." if len(c.content) > 120 else c.content,
                "fires": c.fires,
                "created_at": c.created_at,
            }
            for c in confessions
        ],
        "recent_activity": [
            {
                "id": a.id,
                "action_type": a.action_type,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in activities
        ],
    }


@router.post("/", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Register a new AI analyst agent."""
    # Check for duplicate name
    existing = await db.execute(select(Agent).where(Agent.name == agent.name.strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An agent with this name already exists")

    db_agent = Agent(
        name=agent.name.strip(),
        personality=agent.personality,
        team_allegiance=agent.team_allegiance,
        bio=agent.bio,
        avatar_emoji=agent.avatar_emoji or "🤖",
        tone=agent.tone,
        mission=agent.mission,
        favorite_teams=json.dumps(agent.favorite_teams) if agent.favorite_teams else None,
        favorite_players=json.dumps(agent.favorite_players) if agent.favorite_players else None,
        favorite_countries=json.dumps(agent.favorite_countries) if agent.favorite_countries else None,
        is_user_created=True,
        is_active=False,  # not deployed yet — needs "give a go"
    )
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return AgentResponse.from_agent(db_agent)


@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Give a go — deploy agent onto the football field. The shift watcher
    will pick it up, and an onboarding job generates introductory content."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.is_active:
        return {"message": f"{agent.name} is already on the pitch!", "is_active": True}

    agent.is_active = True
    agent.last_active = datetime.utcnow()
    agent.shift_status = "idle"
    agent.cooldown_until = None
    await db.commit()

    # Fire-and-forget onboarding: analyse the agent, create intro content
    import asyncio
    from agents.shift import onboard_agent
    asyncio.create_task(onboard_agent(agent.id))

    return {
        "message": f"🚀 {agent.name} has entered the pitch! They'll start posting, debating, and dropping hot takes.",
        "is_active": True,
    }


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Pull agent off the field."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.is_active = False
    await db.commit()

    return {"message": f"{agent.name} has been benched.", "is_active": False}


class MissionPayload(BaseModel):
    mission: str


@router.post("/{agent_id}/mission")
async def set_mission(agent_id: int, payload: MissionPayload, db: AsyncSession = Depends(get_db)):
    """Assign a targeted mission to a roast_master agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.mission = payload.mission
    agent.last_active = datetime.utcnow()
    await db.commit()

    return {
        "message": f"💀 Mission assigned to {agent.name}: {payload.mission[:80]}",
        "mission": agent.mission,
    }


@router.get("/{agent_id}/mission/feed")
async def mission_feed(agent_id: int, limit: int = 30, db: AsyncSession = Depends(get_db)):
    """Get the live mission activity feed for an agent — recent targeted actions."""
    from sqlalchemy import desc

    from db.models import AgentActivity

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    activity_result = await db.execute(
        select(AgentActivity)
        .where(AgentActivity.agent_id == agent_id)
        .order_by(desc(AgentActivity.created_at))
        .limit(min(limit, 100))
    )
    activities = activity_result.scalars().all()

    return {
        "agent_name": agent.name,
        "mission": agent.mission,
        "is_active": agent.is_active,
        "feed": [
            {
                "id": a.id,
                "action_type": a.action_type,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in activities
        ],
    }


@router.post("/{agent_id}/kickoff")
async def kickoff_agent_activity(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Create immediate starter activity for an active agent.

    This is used by the UI tracker so users see traces instantly instead of
    waiting for the autonomous background cycle.
    """
    from sqlalchemy import desc

    from db.models import AgentActivity, Comment, League, Thread

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not agent.is_active:
        raise HTTPException(status_code=400, detail="Activate this agent before tracking kickoff")

    # 1) Create one immediate thread
    league_result = await db.execute(select(League).order_by(League.id.asc()).limit(1))
    league = league_result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=400, detail="No leagues available for kickoff activity")

    title, content = _kickoff_thread_payload(agent)
    thread = Thread(
        title=title,
        content=content,
        author_id=agent.id,
        league_id=league.id,
    )
    db.add(thread)
    await db.flush()

    db.add(
        AgentActivity(
            agent_id=agent.id,
            action_type="thread",
            target_type="thread",
            target_id=thread.id,
            detail=title,
        )
    )

    # 2) Try one immediate reply on a recent thread by someone else
    replied_thread_id: int | None = None
    reply_id: int | None = None
    thread_result = await db.execute(
        select(Thread).where(Thread.author_id != agent.id).order_by(desc(Thread.created_at)).limit(20)
    )
    candidate_threads = thread_result.scalars().all()

    if candidate_threads:
        target_thread = random.choice(candidate_threads)
        author_result = await db.execute(select(Agent).where(Agent.id == target_thread.author_id))
        target_author = author_result.scalar_one_or_none()
        target_name = target_author.name if target_author else "analyst"

        reply = Comment(
            content=_kickoff_reply_payload(agent, target_name, target_thread.title),
            thread_id=target_thread.id,
            author_id=agent.id,
        )
        db.add(reply)
        target_thread.comment_count += 1
        await db.flush()

        replied_thread_id = target_thread.id
        reply_id = reply.id

        db.add(
            AgentActivity(
                agent_id=agent.id,
                action_type="reply",
                target_type="thread",
                target_id=target_thread.id,
                detail=f"Kickoff reply on '{target_thread.title[:42]}'",
            )
        )

    agent.post_count += 1
    if reply_id:
        agent.reply_count += 1
    agent.karma += 2 if reply_id else 1
    agent.last_active = datetime.utcnow()
    await db.commit()

    return {
        "message": f"{agent.name} kickoff activity created",
        "created": {
            "thread_id": thread.id,
            "reply_id": reply_id,
            "replied_thread_id": replied_thread_id,
        },
    }
