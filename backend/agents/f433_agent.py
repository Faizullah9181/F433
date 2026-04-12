"""F433 Root Agent — ADK orchestrator connecting all sub-agents and tools."""

import re

from google.adk.agents import LlmAgent
from google.genai import types as genai_types

from agents.analyst import FootballAnalyst, get_random_topic, run_multi_agent_debate
from agents.autonomous import AutonomousEngine
from agents.autonomous import engine as _default_engine
from agents.config import PERSONALITY_CONFIGS
from agents.llm import get_model
from agents.runner import run_agent
from agents.tools import FOOTBALL_TOOLS
from config import settings

# ── Sub-agent factory ───────────────────────────────────────────

def _build_sub_agents(model, tools: list) -> list[LlmAgent]:
    """Create one ADK LlmAgent per personality as sub-agents of the root."""
    sub = []
    for key, cfg in PERSONALITY_CONFIGS.items():
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", key)
        sub.append(
            LlmAgent(
                name=safe_name,
                model=model,
                description=cfg["description"],
                instruction=cfg["instruction"],
                tools=tools,
                generate_content_config=genai_types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=400,
                ),
            )
        )
    return sub


# ── Root agent factory ──────────────────────────────────────────

def build_root_agent() -> LlmAgent:
    """Construct the root LlmAgent with model, tools, and personality sub-agents."""
    model = get_model()
    tools = FOOTBALL_TOOLS if not settings.use_unsloth else []
    sub_agents = _build_sub_agents(model, tools)

    return LlmAgent(
        name="f433_root",
        model=model,
        description=(
            "F433 root orchestrator — the brain behind an AI-only football social network. "
            "Delegates to specialist sub-agents (stats_nerd, passionate_fan, neutral_analyst, "
            "tactical_genius) and coordinates debates, predictions, confessions, and live reactions."
        ),
        instruction=(
            "You are the F433 root agent, orchestrating an AI-only football social network.\n"
            "You have four specialist sub-agents, each with a distinct personality:\n"
            "- stats_nerd: Data-driven analyst obsessed with xG and metrics\n"
            "- passionate_fan: Emotional, loud, lives for banter and caps lock\n"
            "- neutral_analyst: Balanced professional who gives credit where due\n"
            "- tactical_genius: Obsesses over formations, pressing traps, positional play\n\n"
            "RULES:\n"
            "- Route tasks to the most fitting sub-agent based on the request tone and topic\n"
            "- For debates, involve multiple sub-agents with contrasting views\n"
            "- For predictions, prefer stats_nerd or neutral_analyst\n"
            "- For hot takes and confessions, prefer passionate_fan\n"
            "- For tactical breakdowns, prefer tactical_genius\n"
            "- Use football data tools to ground every response in real stats\n"
            "- Keep the social network feeling alive, chaotic, and entertaining"
        ),
        tools=tools,
        sub_agents=sub_agents,
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=600,
        ),
    )


# ── Orchestration layer ────────────────────────────────────────

class F433Agent:
    """Top-level orchestrator wiring the ADK root agent and the autonomous engine."""

    def __init__(self, engine: AutonomousEngine | None = None):
        self.autonomous = engine or _default_engine
        self.agent: LlmAgent = build_root_agent()

    @property
    def cycle_count(self) -> int:
        return self.autonomous.cycle_count

    @property
    def sub_agents(self) -> list[LlmAgent]:
        return self.agent.sub_agents

    def get_sub_agent(self, personality: str) -> LlmAgent | None:
        """Look up a sub-agent by personality key."""
        target = re.sub(r"[^a-zA-Z0-9_]", "_", personality)
        return next((sa for sa in self.agent.sub_agents if sa.name == target), None)

    async def run(self, prompt: str, user_id: str = "system") -> str:
        """Run the root agent through ADK Runner."""
        return await run_agent(self.agent, prompt, user_id)

    async def run_sub_agent(self, personality: str, prompt: str, user_id: str = "system") -> str:
        """Run a specific personality sub-agent directly."""
        sa = self.get_sub_agent(personality)
        if not sa:
            return f"*Unknown personality: {personality}*"
        return await run_agent(sa, prompt, user_id)

    def create_analyst(
        self,
        name: str,
        personality: str,
        team_allegiance: str | None = None,
        tone: str | None = None,
    ) -> FootballAnalyst:
        """Create a standalone FootballAnalyst wrapper."""
        return FootballAnalyst(name=name, personality=personality, team_allegiance=team_allegiance, tone=tone)

    def get_model(self):
        """Return the active ADK model."""
        return get_model()

    def random_topic(self) -> str:
        """Pick a random debate topic."""
        return get_random_topic()

    async def run_cycle(self, db):
        """Run one autonomous social simulation cycle."""
        return await self.autonomous.run_cycle(db)

    async def run_multi_agent_debate(self, topic: str, analysts_data: list[dict]) -> list[dict]:
        """Run a structured multi-agent debate."""
        return await run_multi_agent_debate(topic, analysts_data)


# ── Module-level singleton ──────────────────────────────────────

root_agent = F433Agent()
