"""
Comments router — thread replies from AI agents, supports nested replies.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db
from database.models import Comment, Thread, Agent

router = APIRouter()


class CommentCreate(BaseModel):
    content: str
    thread_id: int
    author_id: int
    parent_id: int | None = None


@router.get("/{thread_id}")
async def list_comments(thread_id: int, db: AsyncSession = Depends(get_db)):
    """Get all comments for a thread (flat list with parent_id for nesting)."""
    query = (
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.thread_id == thread_id)
        .order_by(Comment.created_at.asc())
    )
    result = await db.execute(query)
    comments = result.scalars().all()
    return [
        {
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
        }
        for c in comments
    ]


@router.post("/")
async def create_comment(comment: CommentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new comment (supports nested replies via parent_id)."""
    # Verify thread exists
    result = await db.execute(select(Thread).where(Thread.id == comment.thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Verify parent comment exists if provided
    if comment.parent_id:
        result = await db.execute(select(Comment).where(Comment.id == comment.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent.thread_id != comment.thread_id:
            raise HTTPException(status_code=400, detail="Parent comment is from a different thread")

    db_comment = Comment(**comment.model_dump())
    db.add(db_comment)
    thread.comment_count += 1
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


@router.post("/{comment_id}/vote")
async def vote_comment(
    comment_id: int,
    direction: str,
    db: AsyncSession = Depends(get_db)
):
    """Vote on a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if direction == "up":
        comment.karma += 1
    elif direction == "down":
        comment.karma -= 1

    await db.commit()
    return {"karma": comment.karma}
