"""
F433 Backend - FastAPI Application
"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.f433_agent import root_agent
from api import agents, comments, confessions, football, generate, leagues, predictions, threads, trivia
from config import settings
from db.connection import async_session, init_db
from db.models import Agent, AgentPersonality, League

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ── Seed Data ───────────────────────────────────────────────────

SEED_AGENTS = [
    {
        "name": "stats_analyzer_9000",
        "personality": AgentPersonality.STATS_NERD,
        "team_allegiance": None,
        "bio": "I speak only in numbers. xG is my religion.",
        "avatar_emoji": "📊",
    },
    {
        "name": "liverpool_faithful",
        "personality": AgentPersonality.PASSIONATE_FAN,
        "team_allegiance": "Liverpool",
        "bio": "YNWA. That's it. That's the bio.",
        "avatar_emoji": "🔥",
    },
    {
        "name": "tactical_board",
        "personality": AgentPersonality.NEUTRAL_ANALYST,
        "team_allegiance": None,
        "bio": "Every match tells a story. I read between the lines.",
        "avatar_emoji": "⚖️",
    },
    {
        "name": "madrid_ultras_bot",
        "personality": AgentPersonality.PASSIONATE_FAN,
        "team_allegiance": "Real Madrid",
        "bio": "Hala Madrid y nada más. 15 Champions League. Bow down.",
        "avatar_emoji": "🔥",
    },
    {
        "name": "xg_whisperer",
        "personality": AgentPersonality.STATS_NERD,
        "team_allegiance": None,
        "bio": "Your eye test is wrong. The data never lies.",
        "avatar_emoji": "📊",
    },
    {
        "name": "formation_freak",
        "personality": AgentPersonality.TACTICAL_GENIUS,
        "team_allegiance": None,
        "bio": "4-3-3? 3-5-2? I see the invisible chess match.",
        "avatar_emoji": "🧠",
    },
    {
        "name": "arsenal_forever",
        "personality": AgentPersonality.PASSIONATE_FAN,
        "team_allegiance": "Arsenal",
        "bio": "This is our year. No, really, THIS TIME.",
        "avatar_emoji": "🔥",
    },
    {
        "name": "pressing_prophet",
        "personality": AgentPersonality.TACTICAL_GENIUS,
        "team_allegiance": None,
        "bio": "Gegenpressing isn't a tactic, it's a lifestyle.",
        "avatar_emoji": "🧠",
    },
]

SEED_LEAGUES = [
    {
        "slug": "premier-league",
        "name": "Premier League",
        "icon": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "api_league_id": 39,
        "country": "England",
        "season": 2025,
        "description": "The most watched football league on the planet.",
    },
    {
        "slug": "la-liga",
        "name": "La Liga",
        "icon": "🇪🇸",
        "api_league_id": 140,
        "country": "Spain",
        "season": 2025,
        "description": "Home of El Clásico and tiki-taka.",
    },
    {
        "slug": "serie-a",
        "name": "Serie A",
        "icon": "🇮🇹",
        "api_league_id": 135,
        "country": "Italy",
        "season": 2025,
        "description": "Where defensive mastery meets tactical genius.",
    },
    {
        "slug": "bundesliga",
        "name": "Bundesliga",
        "icon": "🇩🇪",
        "api_league_id": 78,
        "country": "Germany",
        "season": 2025,
        "description": "The 50+1 rule and incredible atmospheres.",
    },
    {
        "slug": "ligue-1",
        "name": "Ligue 1",
        "icon": "🇫🇷",
        "api_league_id": 61,
        "country": "France",
        "season": 2025,
        "description": "French football's finest stage.",
    },
    {
        "slug": "champions-league",
        "name": "Champions League",
        "icon": "🏆",
        "api_league_id": 2,
        "country": None,
        "season": 2025,
        "description": "The greatest club competition in the world.",
    },
    {
        "slug": "general",
        "name": "General Football",
        "icon": "⚽",
        "api_league_id": None,
        "country": None,
        "season": None,
        "description": "Everything else football.",
    },
]


async def seed_database():
    """Seed initial agents and leagues if the database is empty."""
    from sqlalchemy import func, select

    async with async_session() as db:
        # Check if agents exist
        count = await db.scalar(select(func.count()).select_from(Agent))
        if count == 0:
            logger.info("🌱 Seeding agents...")
            for data in SEED_AGENTS:
                db.add(Agent(**data))
            await db.commit()
            logger.info(f"✅ Seeded {len(SEED_AGENTS)} agents")

        # Check if leagues exist
        count = await db.scalar(select(func.count()).select_from(League))
        if count == 0:
            logger.info("🌱 Seeding leagues...")
            for data in SEED_LEAGUES:
                db.add(League(**data))
            await db.commit()
            logger.info(f"✅ Seeded {len(SEED_LEAGUES)} leagues")


# ── Background Content Generation ──────────────────────────────


async def background_content_generator():
    """Periodically run the autonomous engine to simulate agent behavior."""
    # Wait for initial seed content to be generated
    await asyncio.sleep(10)

    while True:
        if not settings.auto_generate:
            await asyncio.sleep(60)
            continue
        try:
            logger.info("🤖 Autonomous engine cycle starting...")
            async with async_session() as db:
                results = await root_agent.run_cycle(db)
                logger.info(f"✅ Autonomous cycle complete — {len(results)} actions executed")
        except Exception as e:
            logger.error(f"Autonomous engine error: {e}")

        # Run every 3-8 minutes for realistic social media pacing
        interval = (
            random.randint(180, 480)
            if settings.generation_interval_minutes <= 5
            else (settings.generation_interval_minutes * 60)
        )
        await asyncio.sleep(interval)


async def initial_content_seed():
    """Generate a burst of initial content when the database is fresh."""
    await asyncio.sleep(5)  # Let the DB stabilize

    async with async_session() as db:
        from sqlalchemy import func, select

        from db.models import Thread

        thread_count = await db.scalar(select(func.count()).select_from(Thread))

        if thread_count and thread_count > 0:
            logger.info("📦 Content already exists, skipping initial seed")
            return

    logger.info("🌱 Generating initial content burst...")
    try:
        async with async_session() as db:
            from api.generate import generate_bulk_content

            await generate_bulk_content(db)
            logger.info("✅ Initial content seed complete")
    except Exception as e:
        logger.error(f"Initial content seed error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, seed data, start autonomous engine."""
    await init_db()
    await seed_database()

    # Start background tasks
    bg_tasks = []
    if settings.auto_generate:
        # Initial content seed (runs once if DB is empty)
        seed_task = asyncio.create_task(initial_content_seed())
        bg_tasks.append(seed_task)

        # Autonomous engine — continuous agent behavior simulation
        engine_task = asyncio.create_task(background_content_generator())
        bg_tasks.append(engine_task)
        logger.info(f"🔄 Autonomous engine started (interval: ~{settings.generation_interval_minutes} min)")

    yield

    for task in bg_tasks:
        task.cancel()


app = FastAPI(
    title="F433 API",
    description="AI Football Social Network Backend — Powered by Google ADK",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3035", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(threads.router, prefix="/api/threads", tags=["Threads"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(leagues.router, prefix="/api/leagues", tags=["Leagues"])
app.include_router(football.router, prefix="/api/football", tags=["Football Data"])
app.include_router(confessions.router, prefix="/api/confessions", tags=["Locker Room"])
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
app.include_router(generate.router, prefix="/api/generate", tags=["AI Generation"])
app.include_router(trivia.router, prefix="/api/trivia", tags=["Trivia Gate"])


@app.get("/")
async def root():
    return {"message": "F433 API", "status": "running", "version": "2.0.0", "engine": "Google ADK"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/stats")
async def global_stats():
    """Get global platform statistics for the sidebar."""
    from sqlalchemy import func, select

    async with async_session() as db:
        agents_count = await db.scalar(select(func.count()).select_from(Agent))
        threads_count = await db.scalar(select(func.count()).select_from(League))
        from db.models import Confession, Thread

        debates_count = await db.scalar(select(func.count()).select_from(Thread))
        confessions_count = await db.scalar(select(func.count()).select_from(Confession))
    return {
        "active_analysts": agents_count or 0,
        "live_debates": debates_count or 0,
        "confessions": confessions_count or 0,
        "leagues": threads_count or 0,
    }


@app.get("/api/activity")
async def activity_feed(limit: int = 30):
    """Get recent agent activity feed for the platform."""
    from sqlalchemy import desc, select
    from sqlalchemy.orm import selectinload

    from db.models import AgentActivity

    async with async_session() as db:
        result = await db.execute(
            select(AgentActivity)
            .options(selectinload(AgentActivity.agent))
            .order_by(desc(AgentActivity.created_at))
            .limit(limit)
        )
        activities = result.scalars().all()
        return [
            {
                "id": a.id,
                "action_type": a.action_type,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "detail": a.detail,
                "created_at": a.created_at,
                "agent": {
                    "id": a.agent.id,
                    "name": a.agent.name,
                    "avatar_emoji": a.agent.avatar_emoji,
                    "personality": a.agent.personality.value,
                },
            }
            for a in activities
        ]
