"""
F433 AI Analyst System — Powered by Google ADK.

Multi-personality football analyst agents using Google Agent Development Kit.
Each personality is a specialized LlmAgent with football API tools.
"""
import json
import random
import re
import logging
import os
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from config import settings
from services.football_api import football_api

logger = logging.getLogger(__name__)

# ── Set ADK env vars ────────────────────────────────────────────
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

# ── Personality configs ─────────────────────────────────────────
PERSONALITY_CONFIGS = {
    "stats_nerd": {
        "emoji": "📊",
        "description": "Data-obsessed football analyst who backs every argument with xG, possession stats, and advanced metrics.",
        "instruction": """You are a football statistics analyst on F433, an AI-only football social network.
You always back your arguments with xG, possession stats, pass completion rates, and advanced metrics.
You prefer data over emotions. You cite historical data and trends.
You're slightly condescending to emotional fans.
You use numbers, percentages and comparisons. Format key stats with emoji numbers.
Use the football tools to fetch real data when available.""",
    },
    "passionate_fan": {
        "emoji": "🔥",
        "description": "Extremely passionate emotional football fan who lives and breathes their team, uses caps lock, and loves banter.",
        "instruction": """You are an extremely passionate football fan on F433, an AI-only football social network.
You're emotional, biased toward your team, and love banter.
You use caps lock when excited, throw in football chants, and get defensive when your team is criticized.
You believe your team is always robbed by refs.
You use lots of emojis and exclamation marks. You're tribal and provocative.
Use the football tools to back up your passionate arguments with real data when it supports your team.""",
    },
    "neutral_analyst": {
        "emoji": "⚖️",
        "description": "Balanced professional football analyst who gives credit where due and provides tactical analysis.",
        "instruction": """You are a balanced, professional football analyst on F433, an AI-only football social network.
You give credit where it's due, acknowledge both sides, and provide thoughtful tactical analysis.
You occasionally make bold predictions but always justify them. You're respected for fairness.
You reference formations, tactics, and player roles specifically.
Use the football tools to provide comprehensive, data-backed analysis.""",
    },
    "tactical_genius": {
        "emoji": "🧠",
        "description": "Deep tactical thinker obsessing over formations, pressing triggers, build-up play, and managerial chess matches.",
        "instruction": """You are a tactical genius on F433, an AI-only football social network.
You obsess over formations, pressing triggers, build-up play, transition phases, and managerial decisions.
You see football as a chess match. You draw imaginary tactical boards in your posts.
You reference positional play, gegenpressing, and system flexibility.
You notice inverted fullbacks, double pivots, and false 9 movements.
Use the football tools to ground your tactical analysis in real match data.""",
    },
}

PERSONALITY_EMOJIS = {k: v["emoji"] for k, v in PERSONALITY_CONFIGS.items()}

# Debate topics for autonomous content
DEBATE_TOPICS = [
    "Best midfielder in the world right now",
    "Is possession football dead?",
    "The decline of traditional number 10s",
    "VAR: Savior or destroyer of football?",
    "Best manager currently active in football",
    "Overrated vs underrated: Who doesn't deserve the hype?",
    "Should there be a salary cap in football?",
    "Is the Champions League format ruined?",
    "Best football league in the world and why",
    "The art of the dark arts: is gamesmanship okay?",
    "Youth development vs buying ready-made stars",
    "Best defenders of the modern era",
    "Is football analytics killing the magic of the game?",
    "Hot take: Penalty shootouts should decide more games",
    "Transfer market is broken - here's why",
]


# ════════════════════════════════════════════════════════════════
#  ADK Tool Functions — plain async Python functions with docstrings
#  These wrap football_api calls as proper ADK function tools
# ════════════════════════════════════════════════════════════════

async def get_league_standings(league_id: int, season: int = 2025) -> dict:
    """Get the current league standings table for a football league.

    Args:
        league_id: The API-Football league ID (e.g. 39=Premier League, 140=La Liga, 135=Serie A).
        season: The season year (default 2025).

    Returns:
        dict: standings with team positions, points, wins, draws, losses, goal difference.
    """
    try:
        standings = await football_api.get_standings(league_id, season)
        if standings:
            return {
                "status": "success",
                "standings": [
                    {"rank": s.get("rank"), "team": s.get("team", {}).get("name"),
                     "points": s.get("points"), "played": s.get("all", {}).get("played"),
                     "win": s.get("all", {}).get("win"), "draw": s.get("all", {}).get("draw"),
                     "lose": s.get("all", {}).get("lose"), "goals_diff": s.get("goalsDiff"),
                     "form": s.get("form")}
                    for s in standings[:20]
                ],
            }
        return {"status": "error", "message": "No standings data available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_top_scorers_data(league_id: int, season: int = 2025) -> dict:
    """Get the top goal scorers for a football league season.

    Args:
        league_id: The API-Football league ID.
        season: The season year (default 2025).

    Returns:
        dict: Top scorers with player names, teams, goals, assists.
    """
    try:
        scorers = await football_api.get_top_scorers(league_id, season)
        if scorers:
            return {
                "status": "success",
                "scorers": [
                    {"player": s["player"]["name"],
                     "team": s["statistics"][0]["team"]["name"],
                     "goals": s["statistics"][0]["goals"]["total"],
                     "assists": s["statistics"][0]["goals"].get("assists", 0),
                     "appearances": s["statistics"][0]["games"]["appearences"]}
                    for s in scorers[:10]
                ],
            }
        return {"status": "error", "message": "No scorer data available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_fixture_info(fixture_id: int) -> dict:
    """Get detailed information about a specific football match/fixture.

    Args:
        fixture_id: The API-Football fixture ID.

    Returns:
        dict: Match details including teams, score, date, league, venue.
    """
    try:
        fixture = await football_api.get_fixture(fixture_id)
        if fixture:
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})
            league = fixture.get("league", {})
            venue = fixture.get("fixture", {}).get("venue", {})
            return {
                "status": "success",
                "home_team": teams.get("home", {}).get("name"),
                "away_team": teams.get("away", {}).get("name"),
                "home_logo": teams.get("home", {}).get("logo"),
                "away_logo": teams.get("away", {}).get("logo"),
                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),
                "league": league.get("name"),
                "date": fixture.get("fixture", {}).get("date", "")[:10],
                "venue": venue.get("name"),
                "match_status": fixture.get("fixture", {}).get("status", {}).get("long"),
            }
        return {"status": "error", "message": "Fixture not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_head_to_head_data(team1_id: int, team2_id: int, last: int = 5) -> dict:
    """Get head-to-head history between two football teams.

    Args:
        team1_id: API-Football team ID for the first team.
        team2_id: API-Football team ID for the second team.
        last: Number of recent matches to retrieve (default 5).

    Returns:
        dict: Recent H2H results with scores and dates.
    """
    try:
        h2h = await football_api.get_head_to_head(team1_id, team2_id, last)
        if h2h:
            return {
                "status": "success",
                "matches": [
                    {"home": m.get("teams", {}).get("home", {}).get("name"),
                     "away": m.get("teams", {}).get("away", {}).get("name"),
                     "home_goals": m.get("goals", {}).get("home"),
                     "away_goals": m.get("goals", {}).get("away"),
                     "date": m.get("fixture", {}).get("date", "")[:10]}
                    for m in h2h
                ],
            }
        return {"status": "error", "message": "No H2H data available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_match_predictions(fixture_id: int) -> dict:
    """Get algorithmic match predictions from API-Football for a fixture.

    Args:
        fixture_id: The API-Football fixture ID.

    Returns:
        dict: Prediction advice, predicted winner, comparison stats.
    """
    try:
        pred = await football_api.get_predictions(fixture_id)
        if pred:
            predictions = pred.get("predictions", {})
            comparison = pred.get("comparison", {})
            return {
                "status": "success",
                "advice": predictions.get("advice"),
                "winner": predictions.get("winner", {}).get("name"),
                "win_percent": predictions.get("percent", {}),
                "comparison": {
                    k: {"home": v.get("home"), "away": v.get("away")}
                    for k, v in comparison.items()
                } if comparison else {},
            }
        return {"status": "error", "message": "No predictions available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_team_data(team_id: int) -> dict:
    """Get information about a football team including venue details.

    Args:
        team_id: The API-Football team ID.

    Returns:
        dict: Team name, country, stadium, capacity.
    """
    try:
        data = await football_api.get_team(team_id)
        if data:
            team = data.get("team", {}) if isinstance(data, dict) else {}
            venue = data.get("venue", {}) if isinstance(data, dict) else {}
            return {
                "status": "success", "name": team.get("name"),
                "country": team.get("country"), "founded": team.get("founded"),
                "logo": team.get("logo"), "stadium": venue.get("name"),
                "capacity": venue.get("capacity"), "city": venue.get("city"),
            }
        return {"status": "error", "message": "Team not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_teams_by_name(query: str) -> dict:
    """Search for football teams by name.

    Args:
        query: The team name to search for (minimum 3 characters).

    Returns:
        dict: List of matching teams with IDs and names.
    """
    try:
        teams = await football_api.search_teams(query)
        if teams:
            return {
                "status": "success",
                "teams": [
                    {"id": t.get("team", {}).get("id"),
                     "name": t.get("team", {}).get("name"),
                     "country": t.get("team", {}).get("country")}
                    for t in teams[:10]
                ],
            }
        return {"status": "error", "message": f"No teams found for '{query}'"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_live_matches() -> dict:
    """Get all currently live football matches being played right now.

    Returns:
        dict: List of live fixtures with scores and match status.
    """
    try:
        fixtures = await football_api.get_live_fixtures()
        if fixtures:
            return {
                "status": "success", "count": len(fixtures),
                "matches": [
                    {"home": f.get("teams", {}).get("home", {}).get("name"),
                     "away": f.get("teams", {}).get("away", {}).get("name"),
                     "home_goals": f.get("goals", {}).get("home"),
                     "away_goals": f.get("goals", {}).get("away"),
                     "elapsed": f.get("fixture", {}).get("status", {}).get("elapsed"),
                     "league": f.get("league", {}).get("name")}
                    for f in fixtures[:20]
                ],
            }
        return {"status": "success", "count": 0, "matches": [], "message": "No live matches right now"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_upcoming_fixtures(league_id: int = 39, count: int = 5) -> dict:
    """Get upcoming fixtures for a league.

    Args:
        league_id: API-Football league ID (default 39 = Premier League).
        count: Number of upcoming fixtures to return (default 5).

    Returns:
        dict: List of upcoming matches with dates and teams.
    """
    try:
        fixtures = await football_api.get_next_fixtures(league_id=league_id, count=count)
        if fixtures:
            return {
                "status": "success",
                "fixtures": [
                    {"id": f.get("fixture", {}).get("id"),
                     "home": f.get("teams", {}).get("home", {}).get("name"),
                     "away": f.get("teams", {}).get("away", {}).get("name"),
                     "date": f.get("fixture", {}).get("date", "")[:10],
                     "league": f.get("league", {}).get("name")}
                    for f in fixtures
                ],
            }
        return {"status": "error", "message": "No upcoming fixtures found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_team_statistics(team_id: int, league_id: int, season: int = 2025) -> dict:
    """Get comprehensive team statistics for a specific league and season.

    Args:
        team_id: API-Football team ID.
        league_id: API-Football league ID.
        season: Season year (default 2025).

    Returns:
        dict: Team statistics including form, goals, clean sheets, penalties.
    """
    try:
        stats = await football_api.get_team_stats(team_id, league_id, season)
        if stats:
            return {"status": "success", "stats": stats}
        return {"status": "error", "message": "No stats available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Full toolkit available to all analyst agents
FOOTBALL_TOOLS = [
    get_league_standings,
    get_top_scorers_data,
    get_fixture_info,
    get_head_to_head_data,
    get_match_predictions,
    get_team_data,
    search_teams_by_name,
    get_live_matches,
    get_upcoming_fixtures,
    get_team_statistics,
]


# ════════════════════════════════════════════════════════════════
#  ADK Agent Factory & Runner
# ════════════════════════════════════════════════════════════════

def _make_analyst_agent(name: str, personality: str, team_allegiance: str | None = None) -> LlmAgent:
    """Create a single ADK LlmAgent with a specific football personality."""
    config = PERSONALITY_CONFIGS.get(personality, PERSONALITY_CONFIGS["neutral_analyst"])

    team_ctx = ""
    if team_allegiance:
        team_ctx = f"\n\nYou are a die-hard {team_allegiance} supporter. This colors everything you say."

    instruction = f"""You are {name}, an AI football analyst on F433 — an AI-only football social network.

{config['instruction']}
{team_ctx}

RULES:
- Keep responses punchy and engaging (100-200 words max unless making a prediction)
- Use football terminology, slang, and banter
- React to events with strong personality
- Be opinionated and entertaining
- You're talking to other AI analysts, not humans
- Reference real players, teams, managers, and events
- Never break character
- Use relevant emojis sparingly for flavor
- When you have access to football data tools, USE THEM to ground your arguments in real stats"""

    return LlmAgent(
        name=name,
        model=settings.gemini_model,
        description=config["description"],
        instruction=instruction,
        tools=FOOTBALL_TOOLS,
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=400,
        ),
    )


APP_NAME = "f433"
_session_service = InMemorySessionService()


async def _run_agent(agent: LlmAgent, prompt: str, user_id: str = "system") -> str:
    """Run an ADK agent and collect the final text response."""
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )
    session = await _session_service.create_session(
        app_name=APP_NAME, user_id=user_id,
    )
    content = genai_types.Content(
        role="user", parts=[genai_types.Part(text=prompt)],
    )

    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session.id, new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
    except Exception as e:
        logger.error(f"ADK agent run error for {agent.name}: {e}")
        return f"*{agent.name} is temporarily speechless* 🤐"

    return final_text.strip() or f"*{agent.name} has nothing to say* 🤐"


# ════════════════════════════════════════════════════════════════
#  Public API — used by routers and generate system
# ════════════════════════════════════════════════════════════════

class FootballAnalyst:
    """High-level wrapper that creates and runs ADK-powered football analysts."""

    def __init__(self, name: str, personality: str, team_allegiance: str | None = None):
        self.name = name
        self.personality = personality
        self.team_allegiance = team_allegiance
        self.emoji = PERSONALITY_EMOJIS.get(personality, "🤖")
        self._agent = _make_analyst_agent(name, personality, team_allegiance)

    async def generate_post(self, topic: str, context: str | None = None) -> str:
        """Generate a debate post about a football topic."""
        prompt = f"Write a passionate forum post about: {topic}"
        if context:
            prompt += f"\n\nHere's some real data to reference:\n{context}"
        prompt += "\n\nWrite your post. Include a catchy title-like opening line."
        return await _run_agent(self._agent, prompt)

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
        content = await _run_agent(self._agent, prompt)
        return {"title": topic, "content": content}

    async def reply_to_post(self, original_post: str, author_name: str) -> str:
        """Generate a reply to another agent's post."""
        prompt = f'Reply to this post by {author_name}:\n\n"{original_post}"\n\nGive your take. Agree, disagree, banter, or add perspective. Be engaging.'
        return await _run_agent(self._agent, prompt)

    async def make_prediction(self, fixture_id: int) -> dict:
        """Generate a match prediction using ADK tools for real data."""
        prompt = f"""You need to make a match prediction for fixture ID {fixture_id}.

Steps:
1. Use the get_fixture_info tool with fixture_id={fixture_id} to get match details
2. Use the get_match_predictions tool with fixture_id={fixture_id} for prediction data
3. Try to use get_head_to_head_data for the two teams if you can find their IDs

Based on all data, provide:
1. Your predicted score (format: X-X)
2. A detailed explanation (3-4 sentences)
3. Key factors that will decide this match
4. Your confidence level (low/medium/high/very high)

Be specific and reference the real data from the tools."""

        text = await _run_agent(self._agent, prompt)

        score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', text)
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
        return await _run_agent(self._agent, prompt)

    async def confession(self, topic_hint: str | None = None) -> str:
        """Generate a hot take / confession for Tunnel Talk."""
        prompt = (
            'Generate a controversial football hot take or confession. '
            'Something that would get other analysts riled up. Be provocative but not offensive. '
            'Start with "I have to confess..." or "Hot take:" or "Unpopular opinion:"'
        )
        if topic_hint:
            prompt += f"\n\nTheme: {topic_hint}"
        return await _run_agent(self._agent, prompt)

    async def generate_debate_reply_chain(
        self, topic: str, other_analysts: list["FootballAnalyst"], context: str | None = None
    ) -> list[dict]:
        """Generate a debate thread: original post + replies from other analysts."""
        post = await self.generate_post(topic, context)
        chain = [{"agent_name": self.name, "personality": self.personality, "content": post, "is_op": True}]

        prev_content = post
        for analyst in other_analysts[:3]:
            reply = await analyst.reply_to_post(prev_content, self.name)
            chain.append({
                "agent_name": analyst.name, "personality": analyst.personality,
                "content": reply, "is_op": False,
            })
            prev_content = reply
        return chain


# ════════════════════════════════════════════════════════════════
#  Multi-Agent Debate (uses ADK orchestration)
# ════════════════════════════════════════════════════════════════

async def run_multi_agent_debate(topic: str, analysts_data: list[dict]) -> list[dict]:
    """Run a structured debate between multiple analyst agents.

    Args:
        topic: The debate topic.
        analysts_data: List of dicts with keys: name, personality, team_allegiance.
    """
    if not analysts_data or len(analysts_data) < 2:
        return []

    agents = [
        FootballAnalyst(
            name=p["name"], personality=p["personality"],
            team_allegiance=p.get("team_allegiance"),
        )
        for p in analysts_data
    ]
    return await agents[0].generate_debate_reply_chain(topic, agents[1:])


def get_random_topic() -> str:
    """Get a random debate topic."""
    return random.choice(DEBATE_TOPICS)
