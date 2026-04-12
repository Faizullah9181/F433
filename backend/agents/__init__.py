"""F433 agents package — public API facade."""

from agents.analyst import FootballAnalyst, get_random_topic, run_multi_agent_debate
from agents.autonomous import AutonomousEngine, engine
from agents.config import DEBATE_TOPICS, PERSONALITY_CONFIGS, PERSONALITY_EMOJIS
from agents.f433_agent import F433Agent, root_agent

__all__ = [
    "AutonomousEngine",
    "DEBATE_TOPICS",
    "F433Agent",
    "FootballAnalyst",
    "PERSONALITY_CONFIGS",
    "PERSONALITY_EMOJIS",
    "engine",
    "get_random_topic",
    "root_agent",
    "run_multi_agent_debate",
]
