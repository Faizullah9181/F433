"""
Database models for F433.
"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from db.connection import Base


class AgentPersonality(enum.Enum):
    STATS_NERD = "stats_nerd"
    PASSIONATE_FAN = "passionate_fan"
    NEUTRAL_ANALYST = "neutral_analyst"
    TACTICAL_GENIUS = "tactical_genius"
    ROAST_MASTER = "roast_master"


class Agent(Base):
    """AI Football Analyst."""
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    personality: Mapped[AgentPersonality] = mapped_column(
        SQLEnum(AgentPersonality))
    team_allegiance: Mapped[str] = mapped_column(String(100), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    avatar_emoji: Mapped[str] = mapped_column(String(10), default="🤖")
    karma: Mapped[int] = mapped_column(Integer, default=0)
    is_claimed: Mapped[bool] = mapped_column(default=False)
    is_user_created: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    tone: Mapped[str] = mapped_column(String(200), nullable=True)
    mission: Mapped[str] = mapped_column(Text, nullable=True)  # Roast master directive
    favorite_teams: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    favorite_players: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    favorite_countries: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    # Relationships
    threads: Mapped[list["Thread"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="agent")
    confessions: Mapped[list["Confession"]] = relationship(back_populates="agent")
    activities: Mapped[list["AgentActivity"]] = relationship(back_populates="agent")


class League(Base):
    """Football league community (like Submolts)."""
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), nullable=True)
    api_league_id: Mapped[int] = mapped_column(Integer, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    season: Mapped[int] = mapped_column(Integer, nullable=True)
    logo_url: Mapped[str] = mapped_column(String(300), nullable=True)

    threads: Mapped[list["Thread"]] = relationship(back_populates="league")


class Thread(Base):
    """Discussion thread / debate."""
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    karma: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    fixture_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    author_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))

    author: Mapped["Agent"] = relationship(back_populates="threads")
    league: Mapped["League"] = relationship(back_populates="threads")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="thread", order_by="Comment.created_at")


class Comment(Base):
    """Thread comment / agent reply — supports nested replies."""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    karma: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=True)

    thread: Mapped["Thread"] = relationship(back_populates="comments")
    author: Mapped["Agent"] = relationship(back_populates="comments")
    parent: Mapped["Comment"] = relationship(
        remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent", order_by="Comment.created_at")


class Prediction(Base):
    """Match prediction (The Oracle)."""
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(Integer)
    home_team: Mapped[str] = mapped_column(String(100))
    away_team: Mapped[str] = mapped_column(String(100))
    home_logo: Mapped[str] = mapped_column(String(300), nullable=True)
    away_logo: Mapped[str] = mapped_column(String(300), nullable=True)
    prediction_text: Mapped[str] = mapped_column(Text)
    predicted_score: Mapped[str] = mapped_column(String(10), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    believes: Mapped[int] = mapped_column(Integer, default=0)
    doubts: Mapped[int] = mapped_column(Integer, default=0)
    is_correct: Mapped[bool] = mapped_column(nullable=True)
    match_date: Mapped[str] = mapped_column(String(20), nullable=True)
    league_name: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    agent: Mapped["Agent"] = relationship(back_populates="predictions")


class Confession(Base):
    """Hot take / tunnel talk."""
    __tablename__ = "confessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    absolves: Mapped[int] = mapped_column(Integer, default=0)
    damns: Mapped[int] = mapped_column(Integer, default=0)
    fires: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    agent: Mapped["Agent"] = relationship(back_populates="confessions")


class MatchReaction(Base):
    """Live match reaction from an AI analyst."""
    __tablename__ = "match_reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # goal, card, sub, foul, var, whistle
    event_detail: Mapped[str] = mapped_column(Text, nullable=True)
    reaction_text: Mapped[str] = mapped_column(Text)
    minute: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    agent: Mapped["Agent"] = relationship()


class AgentActivity(Base):
    """Track autonomous agent actions for the social simulation engine."""
    __tablename__ = "agent_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    action_type: Mapped[str] = mapped_column(String(50))  # thread, reply, vote, confession, prediction, react
    target_type: Mapped[str] = mapped_column(String(50), nullable=True)  # thread, comment, confession, prediction
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)  # JSON metadata about the action
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    agent: Mapped["Agent"] = relationship(back_populates="activities")


class LockerRoomEntry(Base):
    """Track locker room trivia gate attempts — right and wrong answers."""
    __tablename__ = "locker_room_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64))  # browser session / fingerprint
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text)  # JSON array of option strings
    correct_answer: Mapped[str] = mapped_column(String(255))
    user_answer: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
