"""
Analytics router — site visit tracking.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.connection import get_db
from db.models import SiteVisit

logger = logging.getLogger(__name__)

router = APIRouter()


class TrackVisitBody(BaseModel):
    page: str = "/"
    referrer: str | None = None


@router.post("/track")
async def track_visit(
    body: TrackVisitBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Record a page visit."""
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    # Take first IP if multiple forwarded
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    ua = request.headers.get("user-agent", "")[:500]

    visit = SiteVisit(
        page=body.page[:255],
        referrer=(body.referrer or "")[:500] or None,
        user_agent=ua or None,
        ip=ip,
    )
    db.add(visit)
    await db.commit()
    return {"ok": True}


@router.get("/stats")
async def visit_stats(db: AsyncSession = Depends(get_db)):
    """Return total and recent visit counts."""
    total = await db.scalar(select(func.count()).select_from(SiteVisit)) or 0

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = await db.scalar(select(func.count()).select_from(SiteVisit).where(SiteVisit.created_at >= today_start)) or 0

    week_ago = now - timedelta(days=7)
    this_week = (
        await db.scalar(select(func.count()).select_from(SiteVisit).where(SiteVisit.created_at >= week_ago)) or 0
    )

    # Unique IPs as proxy for unique visitors
    unique_total = (
        await db.scalar(
            select(func.count(func.distinct(SiteVisit.ip))).select_from(SiteVisit).where(SiteVisit.ip.isnot(None))
        )
        or 0
    )

    return {
        "total": total,
        "today": today,
        "this_week": this_week,
        "unique_visitors": unique_total,
    }
