"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings


# Convert sync URL to async
DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Initialize database tables."""
    from database import models  # noqa: F401
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add columns introduced after initial schema creation
        migrations = [
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT FALSE",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS tone VARCHAR(200)",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS favorite_teams TEXT",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS favorite_players TEXT",
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS favorite_countries TEXT",
        ]
        for stmt in migrations:
            await conn.execute(text(stmt))


async def get_db():
    """Dependency for getting database sessions."""
    async with async_session() as session:
        yield session
