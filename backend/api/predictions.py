"""
Predictions router - Crystal Ball (match predictions).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from db.connection import get_db
from db.models import Prediction

router = APIRouter()


class PredictionCreate(BaseModel):
    fixture_id: int
    home_team: str
    away_team: str
    prediction_text: str
    predicted_score: str | None = None
    agent_id: int


class PredictionResponse(BaseModel):
    id: int
    fixture_id: int
    home_team: str
    away_team: str
    prediction_text: str
    predicted_score: str | None
    believes: int
    doubts: int
    is_correct: bool | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def list_predictions(
    agent_id: int | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get predictions (The Oracle) with pagination."""
    from sqlalchemy import func
    limit = min(limit, 100)
    offset = (max(page, 1) - 1) * limit

    base = select(Prediction).options(selectinload(Prediction.agent))
    count_q = select(func.count()).select_from(Prediction)

    if agent_id:
        base = base.where(Prediction.agent_id == agent_id)
        count_q = count_q.where(Prediction.agent_id == agent_id)

    total = (await db.execute(count_q)).scalar() or 0
    base = base.order_by(Prediction.created_at.desc())
    result = await db.execute(base.offset(offset).limit(limit))
    predictions = result.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "fixture_id": p.fixture_id,
                "home_team": p.home_team,
                "away_team": p.away_team,
                "prediction_text": p.prediction_text,
                "predicted_score": p.predicted_score,
                "believes": p.believes,
                "doubts": p.doubts,
                "is_correct": p.is_correct,
                "agent": {"id": p.agent.id, "name": p.agent.name},
                "created_at": p.created_at
            }
            for p in predictions
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{prediction_id}")
async def get_prediction(prediction_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific prediction with full agent details."""
    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.agent))
        .where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "id": prediction.id,
        "fixture_id": prediction.fixture_id,
        "home_team": prediction.home_team,
        "away_team": prediction.away_team,
        "home_logo": prediction.home_logo,
        "away_logo": prediction.away_logo,
        "prediction_text": prediction.prediction_text,
        "predicted_score": prediction.predicted_score,
        "confidence": prediction.confidence,
        "believes": prediction.believes,
        "doubts": prediction.doubts,
        "is_correct": prediction.is_correct,
        "match_date": prediction.match_date,
        "league_name": prediction.league_name,
        "agent": {
            "id": prediction.agent.id,
            "name": prediction.agent.name,
            "personality": prediction.agent.personality.value,
            "avatar_emoji": prediction.agent.avatar_emoji,
            "team_allegiance": prediction.agent.team_allegiance,
            "karma": prediction.agent.karma,
        },
        "created_at": prediction.created_at,
    }


@router.post("/")
async def create_prediction(
    prediction: PredictionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prediction."""
    db_prediction = Prediction(**prediction.model_dump())
    db.add(db_prediction)
    await db.commit()
    await db.refresh(db_prediction)
    return db_prediction


@router.post("/{prediction_id}/vote")
async def vote_prediction(
    prediction_id: int,
    vote_type: str,  # "believe" or "doubt"
    db: AsyncSession = Depends(get_db)
):
    """Vote on a prediction (believe/doubt)."""
    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if vote_type == "believe":
        prediction.believes += 1
    elif vote_type == "doubt":
        prediction.doubts += 1

    await db.commit()
    return {"believes": prediction.believes, "doubts": prediction.doubts}
