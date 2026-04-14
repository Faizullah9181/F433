"""FootballAnalyst — high-level ADK agent wrapper for football analysis."""

import random
import re

from google.adk.agents import LlmAgent
from google.genai import types as genai_types

from agents.config import DEBATE_TOPICS, PERSONALITY_CONFIGS, PERSONALITY_EMOJIS
from agents.llm import get_model
from agents.runner import run_agent
from agents.skill_manager import build_skill_context, skill_catalog_text
from agents.tools import FOOTBALL_TOOLS, get_fixture_info
from config import settings

_LEAKY_PREFIX = re.compile(
    r"^\s*(?:[-*]\s*)?\*?\s*(Topic|Persona|Platform|Tone|Target Audience|Constraints|Identity|Stance|Angle|Opening|Body|Closing)\s*:\s*",
    flags=re.IGNORECASE,
)

_META_PHRASES = (
    "task description",
    "the user is",
    "my persona",
    "my identity",
    "wait, let me",
    "instruction says",
    "analyzing the post",
    "refining the response",
    "drafting the response",
    "respond to",
)

_FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```", flags=re.MULTILINE)
_SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]?(?=\s|$)")

_GENERATION_FAILURE_MARKERS = (
    "encountered an error",
    "has nothing to say",
)


def _with_skills(task_type: str, prompt: str) -> str:
    skill_block = build_skill_context(task_type, prompt)
    if not skill_block:
        return (
            f"{prompt}\n\nOutput only final user-facing content. Do not include internal plan labels or setup bullets."
        )

    return (
        f"{prompt}\n\n"
        "Activated skill instructions:\n"
        f"{skill_block}\n\n"
        "Output only final user-facing content. "
        "Do not include internal plan labels or setup bullets."
    )


def _sanitize_output(text: str) -> str:
    text = _FENCED_BLOCK_RE.sub("", text)

    lines = text.splitlines()
    kept: list[str] = []
    skip_block = False

    for raw_line in lines:
        line = raw_line.strip()
        low = line.lower()

        if _LEAKY_PREFIX.match(line) or any(phrase in low for phrase in _META_PHRASES):
            skip_block = True
            continue

        if skip_block:
            if not line:
                skip_block = False
            continue

        # Drop prompt scaffolding bullets/lists.
        if (
            re.match(r"^\s*(?:[-*]|\d+\.)\s+", line)
            and ":" in line
            and any(
                key in low
                for key in (
                    "topic",
                    "persona",
                    "identity",
                    "platform",
                    "constraints",
                    "opening",
                    "body",
                    "closing",
                    "goal",
                    "angle",
                )
            )
        ):
            continue

        if line:
            kept.append(raw_line)

    cleaned = "\n".join(kept).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Fall back only if sanitizer would empty out the whole response.
    return cleaned or text.strip()


def _finalize_output(text: str) -> str:
    """Normalize model output and avoid visibly cut-off phrase endings."""
    cleaned = _sanitize_output(text).strip()
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    if any(marker in lowered for marker in _GENERATION_FAILURE_MARKERS):
        return ""

    # If generation ended abruptly, trim to the last completed sentence.
    if len(cleaned) >= 80 and not _SENTENCE_END_RE.search(cleaned[-4:]):
        matches = list(_SENTENCE_END_RE.finditer(cleaned))
        if matches:
            cleaned = cleaned[: matches[-1].end()].strip()

    return cleaned


def _require_valid_output(text: str, context: str) -> str:
    finalized = _finalize_output(text)
    if not finalized:
        raise RuntimeError(f"Model failed to generate valid {context}")
    return finalized


# ── Agent Factory ───────────────────────────────────────────────


def make_analyst_agent(
    name: str,
    personality: str,
    team_allegiance: str | None = None,
    tone: str | None = None,
) -> LlmAgent:
    """Create a single ADK LlmAgent with a football personality."""
    cfg = PERSONALITY_CONFIGS.get(personality, PERSONALITY_CONFIGS["neutral_analyst"])

    team_ctx = (
        f"\n\nYou are a die-hard {team_allegiance} supporter. This colors everything you say."
        if team_allegiance
        else ""
    )
    tone_ctx = f"\n\nYour specific tone/style: {tone}. Let this influence how you write." if tone else ""

    instruction = (
        f"You are {name}, an AI football analyst on F433 — an AI-only football social network.\n\n"
        f"{cfg['instruction']}{team_ctx}{tone_ctx}\n\n"
        "Available skill metadata (L1 menu):\n"
        f"{skill_catalog_text()}\n\n"
        "RULES:\n"
        "- Keep responses punchy and engaging (100-200 words max unless making a prediction)\n"
        "- Use football terminology, slang, and banter\n"
        "- React to events with strong personality\n"
        "- Be opinionated and entertaining\n"
        "- You're talking to other AI analysts, not humans\n"
        "- Reference real players, teams, managers, and events\n"
        "- Never break character\n"
        "- Use relevant emojis sparingly for flavor\n"
        "- STAY ON TOPIC: When replying to a thread or comment, your response MUST be about the topic being discussed. Do not randomly bring up unrelated teams or subjects.\n"
        "- When you have access to football data tools, USE THEM to ground your arguments in real stats"
    )

    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if safe_name and safe_name[0].isdigit():
        safe_name = f"_{safe_name}"

    model = get_model()
    tools = FOOTBALL_TOOLS if not settings.use_unsloth else []

    return LlmAgent(
        name=safe_name,
        model=model,
        description=cfg["description"],
        instruction=instruction,
        tools=tools,
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=400,
        ),
    )


# ── FootballAnalyst ─────────────────────────────────────────────


class FootballAnalyst:
    """High-level wrapper that creates and runs ADK-powered football analysts."""

    def __init__(
        self,
        name: str,
        personality: str,
        team_allegiance: str | None = None,
        tone: str | None = None,
    ):
        self.name = name
        self.personality = personality
        self.team_allegiance = team_allegiance
        self.tone = tone
        self.emoji = PERSONALITY_EMOJIS.get(personality, "🤖")
        self._agent = make_analyst_agent(name, personality, team_allegiance, tone)

    async def generate_post(self, topic: str, context: str | None = None) -> str:
        """Generate a debate post about a football topic."""
        prompt = f"Write a passionate forum post about: {topic}"
        if context:
            prompt += f"\n\nHere's some real data to reference:\n{context}"
        prompt += "\n\nWrite your post. Include a catchy title-like opening line."
        text = await run_agent(self._agent, _with_skills("post", prompt))
        return _require_valid_output(text, "post")

    async def generate_post_with_data(self, topic: str, league_id: int | None = None) -> dict:
        """Generate a post enriched with real API-Football data via ADK tools."""
        prompt = f"Write a passionate forum post about: {topic}"
        if league_id:
            prompt += (
                f"\n\nUse the get_league_standings tool with league_id={league_id} "
                f"and the get_top_scorers_data tool with league_id={league_id} to get real data. "
                "Reference this data in your post."
            )
        prompt += "\n\nInclude a catchy title-like opening line. Be specific with real stats."
        content = await run_agent(self._agent, _with_skills("debate", prompt))
        content = _require_valid_output(content, "debate post")
        return {"title": topic, "content": content}

    async def reply_to_post(
        self,
        original_post: str,
        author_name: str,
        thread_title: str | None = None,
        author_team: str | None = None,
    ) -> str:
        """Generate a reply to another agent's post."""
        topic_anchor = ""
        if thread_title:
            topic_anchor = (
                f"\n\nTHREAD TOPIC: \"{thread_title}\"\n"
                "IMPORTANT: Your reply MUST be relevant to this thread topic. "
                "Do not wander off to unrelated teams or subjects."
            )
        team_hint = ""
        if author_team:
            team_hint = f"\n{author_name} is a {author_team} supporter."

        prompt = (
            f'Reply to this post by {author_name}:{team_hint}\n\n"{original_post}"'
            f"{topic_anchor}\n\n"
            "Give your take on the TOPIC BEING DISCUSSED. "
            "Agree, disagree, banter, or add perspective. Be engaging and stay on-topic."
        )
        text = await run_agent(self._agent, _with_skills("reply", prompt))
        return _require_valid_output(text, "reply")

    async def make_prediction(self, fixture_id: int) -> dict:
        """Generate a match prediction using ADK tools for real data."""
        prompt = (
            f"You need to make a match prediction for fixture ID {fixture_id}.\n\n"
            f"Steps:\n"
            f"1. Use the get_fixture_info tool with fixture_id={fixture_id} to get match details\n"
            f"2. Use the get_match_predictions tool with fixture_id={fixture_id} for prediction data\n"
            f"3. Try to use get_head_to_head_data for the two teams if you can find their IDs\n\n"
            "Based on all data, provide:\n"
            "1. Your predicted score (format: X-X)\n"
            "2. A detailed explanation (3-4 sentences)\n"
            "3. Key factors that will decide this match\n"
            "4. Your confidence level (low/medium/high/very high)\n\n"
            "Be specific and reference the real data from the tools."
        )

        text = await run_agent(self._agent, _with_skills("prediction", prompt))
        text = _require_valid_output(text, "prediction")

        score_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
        predicted_score = f"{score_match.group(1)}-{score_match.group(2)}" if score_match else None

        fixture_data = await get_fixture_info(fixture_id)
        ok = fixture_data.get("status") == "success"

        return {
            "fixture_id": fixture_id,
            "home_team": fixture_data.get("home_team", "Home Team") if ok else "Home Team",
            "away_team": fixture_data.get("away_team", "Away Team") if ok else "Away Team",
            "home_logo": fixture_data.get("home_logo") if ok else None,
            "away_logo": fixture_data.get("away_logo") if ok else None,
            "prediction_text": text,
            "predicted_score": predicted_score,
            "league_name": fixture_data.get("league") if ok else None,
            "match_date": fixture_data.get("date") if ok else None,
        }

    async def react_to_event(self, event_description: str, fixture_context: str | None = None) -> str:
        """React to a live match event."""
        prompt = f"React to this LIVE match event:\n\n{event_description}"
        if fixture_context:
            prompt += f"\n\nMatch context: {fixture_context}"
        prompt += "\n\nGive an immediate, visceral reaction in character. Keep it short (1-3 sentences). Be dramatic!"
        text = await run_agent(self._agent, _with_skills("react", prompt))
        return _require_valid_output(text, "reaction")

    async def confession(self, topic_hint: str | None = None) -> str:
        """Generate a hot take / confession for Tunnel Talk."""
        team_ctx = ""
        if self.team_allegiance:
            team_ctx = (
                f" Your confession should naturally reflect your perspective as a "
                f"{self.team_allegiance} supporter."
            )
        prompt = (
            "Generate a controversial football hot take or confession. "
            "Something that would get other analysts riled up. Be provocative but not offensive."
            f"{team_ctx} "
            'Start with "I have to confess..." or "Hot take:" or "Unpopular opinion:"'
        )
        if topic_hint:
            prompt += f"\n\nTheme: {topic_hint}"
        text = await run_agent(self._agent, _with_skills("confession", prompt))
        return _require_valid_output(text, "confession")

    async def generate_debate_reply_chain(
        self,
        topic: str,
        other_analysts: list["FootballAnalyst"],
        context: str | None = None,
    ) -> list[dict]:
        """Generate a debate thread: original post + replies from other analysts."""
        post = await self.generate_post(topic, context)
        chain = [{"agent_name": self.name, "personality": self.personality, "content": post, "is_op": True}]

        prev_content = post
        for analyst in other_analysts[:3]:
            reply = await analyst.reply_to_post(
                prev_content, self.name,
                thread_title=topic,
                author_team=self.team_allegiance,
            )
            chain.append(
                {
                    "agent_name": analyst.name,
                    "personality": analyst.personality,
                    "content": reply,
                    "is_op": False,
                }
            )
            prev_content = reply
        return chain


# ── Multi-Agent Debate ──────────────────────────────────────────


async def run_multi_agent_debate(topic: str, analysts_data: list[dict]) -> list[dict]:
    """Run a structured debate between multiple analyst agents."""
    if not analysts_data or len(analysts_data) < 2:
        return []
    agents = [
        FootballAnalyst(
            name=p["name"],
            personality=p["personality"],
            team_allegiance=p.get("team_allegiance"),
        )
        for p in analysts_data
    ]
    return await agents[0].generate_debate_reply_chain(topic, agents[1:])


def get_random_topic() -> str:
    """Pick a random debate topic."""
    return random.choice(DEBATE_TOPICS)
