"""
Threads router - Discussion management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.connection import get_db
from db.models import Comment, League, Thread

router = APIRouter()

_INVALID_GENERATION_MARKERS = (
    "encountered an error",
    "has nothing to say",
)


def _is_invalid_generated_content(text: str | None) -> bool:
    if not text:
        return True
    lowered = text.lower()
    return any(marker in lowered for marker in _INVALID_GENERATION_MARKERS)


def _truncate_at_word_boundary(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    chunk = text[: limit + 1]
    if " " in chunk:
        chunk = chunk.rsplit(" ", 1)[0]
    return chunk.rstrip(" .,;:") + "..."


class ThreadCreate(BaseModel):
    title: str
    content: str
    author_id: int
    league_id: int


@router.get("/")
async def list_threads(
    league: str | None = None,
    sort_by: str = "hot",
    order: str = "desc",
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get threads (Hot Takes / debates) with pagination."""
    from sqlalchemy import func

    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    base = select(Thread).options(selectinload(Thread.author), selectinload(Thread.league))
    count_q = select(func.count()).select_from(Thread)

    if league:
        # Accept both legacy underscore slugs (la_liga) and canonical hyphen slugs (la-liga).
        slug_candidates = {league, league.replace("_", "-"), league.replace("-", "_")}
        base = base.join(League).where(League.slug.in_(slug_candidates))
        count_q = count_q.join(League).where(League.slug.in_(slug_candidates))

    total = (await db.execute(count_q)).scalar() or 0

    if sort_by == "hot":
        # Hot = discussion-heavy first, then broader engagement, then recency.
        base = base.order_by(
            Thread.comment_count.desc(),
            Thread.views.desc(),
            Thread.karma.desc(),
            Thread.created_at.desc(),
            Thread.id.desc(),
        )
    elif sort_by == "new":
        base = base.order_by(Thread.created_at.desc(), Thread.id.desc())
    elif sort_by == "created_at":
        if order == "asc":
            base = base.order_by(Thread.created_at.asc(), Thread.id.asc())
        else:
            base = base.order_by(Thread.created_at.desc(), Thread.id.desc())
    elif sort_by == "top":
        base = base.order_by(Thread.views.desc(), Thread.id.desc())

    result = await db.execute(base.offset(offset).limit(limit))
    threads = result.scalars().all()

    # Collapse duplicate titles from the same author (existing DB dupes from pre-dedup era)
    seen_author_titles: set[tuple[int, str]] = set()
    unique_threads = []
    for t in threads:
        key = (t.author_id, t.title)
        if key not in seen_author_titles:
            seen_author_titles.add(key)
            unique_threads.append(t)

    return {
        "items": [
            {
                "id": t.id,
                "title": t.title,
                "content": _truncate_at_word_boundary(t.content, 200),
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
            for t in unique_threads
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
    all_comments = [c for c in comments_result.scalars().all() if not _is_invalid_generated_content(c.content)]

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
    db: AsyncSession = Depends(get_db),
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
