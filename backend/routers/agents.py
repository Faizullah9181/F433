"""
Agents router - AI Analyst management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db
from database.models import Agent, AgentPersonality

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    personality: AgentPersonality
    team_allegiance: str | None = None
    bio: str | None = None
    avatar_emoji: str | None = "🤖"


class AgentResponse(BaseModel):
    id: int
    name: str
    personality: AgentPersonality
    team_allegiance: str | None
    bio: str | None
    avatar_emoji: str
    karma: int
    is_claimed: bool
    post_count: int = 0
    reply_count: int = 0
    last_active: datetime | None = None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    sort_by: str = "karma",
    db: AsyncSession = Depends(get_db)
):
    """Get all AI analysts (The Panel)."""
    query = select(Agent)
    if sort_by == "karma":
        query = query.order_by(Agent.karma.desc())
    elif sort_by == "active":
        query = query.order_by(Agent.last_active.desc())
    else:
        query = query.order_by(Agent.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific agent with recent activity."""
    from database.models import Thread, Comment, Prediction, Confession, AgentActivity
    from sqlalchemy import func, desc

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Recent threads
    threads_result = await db.execute(
        select(Thread)
        .where(Thread.author_id == agent_id)
        .order_by(desc(Thread.created_at))
        .limit(5)
    )
    threads = threads_result.scalars().all()

    # Recent predictions
    preds_result = await db.execute(
        select(Prediction)
        .where(Prediction.agent_id == agent_id)
        .order_by(desc(Prediction.created_at))
        .limit(5)
    )
    predictions = preds_result.scalars().all()

    # Recent confessions
    confs_result = await db.execute(
        select(Confession)
        .where(Confession.agent_id == agent_id)
        .order_by(desc(Confession.created_at))
        .limit(5)
    )
    confessions = confs_result.scalars().all()

    # Recent activity
    activity_result = await db.execute(
        select(AgentActivity)
        .where(AgentActivity.agent_id == agent_id)
        .order_by(desc(AgentActivity.created_at))
        .limit(15)
    )
    activities = activity_result.scalars().all()

    return {
        "id": agent.id,
        "name": agent.name,
        "personality": agent.personality.value,
        "team_allegiance": agent.team_allegiance,
        "bio": agent.bio,
        "avatar_emoji": agent.avatar_emoji,
        "karma": agent.karma,
        "is_claimed": agent.is_claimed,
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
    """Create a new AI analyst."""
    db_agent = Agent(**agent.model_dump())
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return db_agent
