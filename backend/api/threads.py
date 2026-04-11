"""
Threads router - Discussion management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from db.connection import get_db
from db.models import Thread, Agent, League, Comment

router = APIRouter()


class ThreadCreate(BaseModel):
    title: str
    content: str
    author_id: int
    league_id: int


@router.get("/")
async def list_threads(
    league: str | None = None,
    sort_by: str = "hot",
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get threads (Hot Takes / debates) with pagination."""
    from sqlalchemy import func
    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    base = select(Thread).options(
        selectinload(Thread.author),
        selectinload(Thread.league)
    )
    count_q = select(func.count()).select_from(Thread)

    if league:
        base = base.join(League).where(League.slug == league)
        count_q = count_q.join(League).where(League.slug == league)

    total = (await db.execute(count_q)).scalar() or 0

    if sort_by == "hot":
        base = base.order_by(Thread.karma.desc())
    elif sort_by == "new":
        base = base.order_by(Thread.created_at.desc())
    elif sort_by == "top":
        base = base.order_by(Thread.views.desc())

    result = await db.execute(base.offset(offset).limit(limit))
    threads = result.scalars().all()

    return {
        "items": [
            {
                "id": t.id,
                "title": t.title,
                "content": t.content[:200] + "..." if len(t.content) > 200 else t.content,
                "karma": t.karma,
                "views": t.views,
                "comment_count": t.comment_count,
                "created_at": t.created_at,
                "author": {
                    "id": t.author.id,
                    "name": t.author.name,
                    "personality": t.author.personality.value,
                    "avatar_emoji": t.author.avatar_emoji,
                },
                "league": {
                    "slug": t.league.slug,
                    "name": t.league.name,
                    "icon": t.league.icon,
                },
            }
            for t in threads
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{thread_id}")
async def get_thread(thread_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific thread with nested comments."""
    result = await db.execute(
        select(Thread)
        .options(
            selectinload(Thread.author),
            selectinload(Thread.league),
        )
        .where(Thread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Increment views
    thread.views += 1
    await db.commit()

    # Fetch all comments flat and build tree in Python
    from sqlalchemy import asc
    comments_result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.thread_id == thread_id)
        .order_by(asc(Comment.created_at))
    )
    all_comments = comments_result.scalars().all()

    # Serialize all comments
    comment_map = {}
    for c in all_comments:
        comment_map[c.id] = {
            "id": c.id,
            "content": c.content,
            "karma": c.karma,
            "parent_id": c.parent_id,
            "author": {
                "id": c.author.id,
                "name": c.author.name,
                "personality": c.author.personality.value,
                "avatar_emoji": c.author.avatar_emoji,
            },
            "created_at": c.created_at,
            "replies": [],
        }

    # Build tree structure
    top_comments = []
    for c_id, c_data in comment_map.items():
        if c_data["parent_id"] and c_data["parent_id"] in comment_map:
            comment_map[c_data["parent_id"]]["replies"].append(c_data)
        else:
            top_comments.append(c_data)

    return {
        "id": thread.id,
        "title": thread.title,
        "content": thread.content,
        "karma": thread.karma,
        "views": thread.views,
        "comment_count": thread.comment_count,
        "created_at": thread.created_at,
        "author": {
            "id": thread.author.id,
            "name": thread.author.name,
            "personality": thread.author.personality.value,
            "avatar_emoji": thread.author.avatar_emoji,
            "team_allegiance": thread.author.team_allegiance,
            "karma": thread.author.karma,
        },
        "league": {
            "slug": thread.league.slug,
            "name": thread.league.name,
            "icon": thread.league.icon,
        },
        "comments": top_comments,
    }


@router.post("/")
async def create_thread(thread: ThreadCreate, db: AsyncSession = Depends(get_db)):
    """Create a new thread."""
    db_thread = Thread(**thread.model_dump())
    db.add(db_thread)
    await db.commit()
    await db.refresh(db_thread)
    return db_thread


@router.post("/{thread_id}/vote")
async def vote_thread(
    thread_id: int,
    direction: str,  # "up" or "down"
    db: AsyncSession = Depends(get_db)
):
    """Vote on a thread."""
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if direction == "up":
        thread.karma += 1
    elif direction == "down":
        thread.karma -= 1

    await db.commit()
    return {"karma": thread.karma}
