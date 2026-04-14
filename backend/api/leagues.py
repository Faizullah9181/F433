"""
Leagues router - Community management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.connection import get_db
from db.models import League

router = APIRouter()


class LeagueCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    api_league_id: int | None = None


class LeagueResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    icon: str | None
    api_league_id: int | None
    country: str | None = None
    logo_url: str | None = None

    class Config:
        from_attributes = True


@router.get("/")
async def list_leagues(page: int = 1, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get leagues (communities) with pagination."""
    from sqlalchemy import func

    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    total = (await db.execute(select(func.count()).select_from(League))).scalar() or 0
    result = await db.execute(select(League).order_by(League.id.asc()).offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [LeagueResponse.model_validate(l).model_dump() for l in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(league_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single league by ID."""
    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league


@router.get("/slug/{slug}", response_model=LeagueResponse)
async def get_league_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single league by slug."""
    result = await db.execute(select(League).where(League.slug == slug))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league


@router.post("/", response_model=LeagueResponse)
async def create_league(league: LeagueCreate, db: AsyncSession = Depends(get_db)):
    """Create a new league community."""
    db_league = League(**league.model_dump())
    db.add(db_league)
    await db.commit()
    await db.refresh(db_league)
    return db_league
