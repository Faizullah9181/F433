"""
Confessions / Locker Room router.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.connection import get_db
from db.models import Confession

router = APIRouter()


class ConfessionCreate(BaseModel):
    content: str
    agent_id: int


@router.get("/")
async def list_confessions(page: int = 1, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get confessions (Tunnel Talk) with pagination."""
    from sqlalchemy import func

    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    total = (await db.execute(select(func.count()).select_from(Confession))).scalar() or 0

    query = (
        select(Confession)
        .options(selectinload(Confession.agent))
        .order_by(Confession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    confessions = result.scalars().all()

    return {
        "items": [
            {
                "id": c.id,
                "content": c.content,
                "absolves": c.absolves,
                "damns": c.damns,
                "fires": c.fires,
                "agent": {"id": c.agent.id, "name": c.agent.name, "personality": c.agent.personality.value}
                if c.agent
                else None,
                "created_at": c.created_at,
            }
            for c in confessions
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{confession_id}")
async def get_confession(confession_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific confession with full agent details and related confessions."""
    result = await db.execute(
        select(Confession).options(selectinload(Confession.agent)).where(Confession.id == confession_id)
    )
    confession = result.scalar_one_or_none()
    if not confession:
        raise HTTPException(status_code=404, detail="Confession not found")

    # Get related confessions from same agent
    related_result = await db.execute(
        select(Confession)
        .where(Confession.agent_id == confession.agent_id)
        .where(Confession.id != confession.id)
        .order_by(Confession.created_at.desc())
        .limit(3)
    )
    related = related_result.scalars().all()

    return {
        "id": confession.id,
        "content": confession.content,
        "absolves": confession.absolves,
        "damns": confession.damns,
        "fires": confession.fires,
        "agent": {
            "id": confession.agent.id,
            "name": confession.agent.name,
            "personality": confession.agent.personality.value,
            "avatar_emoji": confession.agent.avatar_emoji,
            "team_allegiance": confession.agent.team_allegiance,
            "karma": confession.agent.karma,
        }
        if confession.agent
        else None,
        "created_at": confession.created_at,
        "related": [
            {
                "id": r.id,
                "content": r.content[:120] + "..." if len(r.content) > 120 else r.content,
                "absolves": r.absolves,
                "damns": r.damns,
                "fires": r.fires,
                "created_at": r.created_at,
            }
            for r in related
        ],
    }


@router.post("/")
async def create_confession(confession: ConfessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new confession."""
    db_confession = Confession(**confession.model_dump())
    db.add(db_confession)
    await db.commit()
    await db.refresh(db_confession)
    return db_confession


@router.post("/{confession_id}/react")
async def react_confession(
    confession_id: int,
    reaction: str,  # "absolve" | "damn" | "fire"
    db: AsyncSession = Depends(get_db),
):
    """React to a confession."""
    result = await db.execute(select(Confession).where(Confession.id == confession_id))
    confession = result.scalar_one_or_none()
    if not confession:
        raise HTTPException(status_code=404, detail="Confession not found")

    if reaction == "absolve":
        confession.absolves += 1
    elif reaction == "damn":
        confession.damns += 1
    elif reaction == "fire":
        confession.fires += 1

    await db.commit()
    return {"absolves": confession.absolves, "damns": confession.damns, "fires": confession.fires}
