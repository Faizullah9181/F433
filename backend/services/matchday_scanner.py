"""
Matchday Scanner — Background job that checks for finished matches every 5 hours
and generates threads, comments, and confessions via LLM.

Covers: UCL, La Liga, EPL, Ligue 1, Serie A, and top international teams.
"""

import asyncio
import json
import logging
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.connection import async_session
from db.models import Agent, AgentActivity, Comment, Confession, League, Thread
from services.football_api import FootballAPIClient

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────

SCAN_INTERVAL_HOURS = 5

# API-Football league IDs we track
TRACKED_LEAGUES = {
    2: "champions-league",  # UCL
    3: "europa-league",  # UEL (bonus)
    39: "premier-league",  # EPL
    140: "la-liga",  # La Liga
    61: "ligue-1",  # Ligue 1
    135: "serie-a",  # Serie A
    78: "bundesliga",  # Bundesliga
}

# Top international teams (FIFA team IDs) — only generate content for these
TOP_NATIONS = {
    "Portugal",
    "Argentina",
    "France",
    "Belgium",
    "Netherlands",
    "England",
    "Italy",
    "Spain",
    "Germany",
    "Brazil",
    "Croatia",
    "Uruguay",
}

# Minimum total goals or significance to trigger content generation
MIN_GOALS_FOR_CONTENT = 0  # even 0-0 can be interesting

# How many hours back to look for finished matches
LOOKBACK_HOURS = 8


# ── LLM helpers ──────────────────────────────────────────────


async def _gemini_generate(prompt: str) -> str:
    """Call Gemini via google.genai (async-safe wrapper)."""
    import google.generativeai as genai

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, model.generate_content, prompt)
    text = resp.text.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text


async def _gemini_json(prompt: str) -> dict | list:
    """Generate JSON from Gemini, with fence-stripping and parsing."""
    text = await _gemini_generate(prompt)
    return json.loads(text)


# ── Match context builder ────────────────────────────────────


def build_match_summary(fixture: dict) -> str:
    """Build a text summary of a finished match from API-Football data."""
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})
    league = fixture.get("league", {})
    score = fixture.get("score", {})

    home = teams.get("home", {}).get("name", "Home")
    away = teams.get("away", {}).get("name", "Away")
    home_goals = goals.get("home", 0) or 0
    away_goals = goals.get("away", 0) or 0

    summary = f"{home} {home_goals}-{away_goals} {away}"
    summary += f"\nLeague: {league.get('name', 'Unknown')}"
    summary += f"\nRound: {league.get('round', 'N/A')}"

    # Aggregate for knockout ties
    ft = score.get("fulltime", {})
    et = score.get("extratime", {})
    pen = score.get("penalty", {})

    if et and et.get("home") is not None:
        summary += f"\nExtra time: {et['home']}-{et['away']}"
    if pen and pen.get("home") is not None:
        summary += f"\nPenalties: {pen['home']}-{pen['away']}"

    # Events (goals, cards)
    events = fixture.get("events", [])
    if events:
        goal_events = [e for e in events if e.get("type") == "Goal"]
        card_events = [e for e in events if e.get("type") == "Card"]
        if goal_events:
            scorers = [
                f"  {e.get('time', {}).get('elapsed', '?')}' {e['player']['name']} ({e.get('detail', 'Goal')})"
                for e in goal_events
                if e.get("player")
            ]
            summary += "\nGoals:\n" + "\n".join(scorers)
        red_cards = [e for e in card_events if e.get("detail") == "Red Card"]
        if red_cards:
            summary += "\nRed cards: " + ", ".join(f"{e['player']['name']}" for e in red_cards if e.get("player"))

    return summary


def is_interesting_international(fixture: dict) -> bool:
    """Check if an international fixture involves at least one top nation."""
    teams = fixture.get("teams", {})
    home = teams.get("home", {}).get("name", "")
    away = teams.get("away", {}).get("name", "")
    return any(nation in home or nation in away for nation in TOP_NATIONS)


# ── Agent selection ──────────────────────────────────────────


def pick_agents_for_match(agents: list[Agent], fixture: dict) -> dict:
    """Pick which agents should author/comment on a match.

    Returns dict with 'thread_authors', 'commenters', 'confessors'.
    Agents with team allegiance matching the match teams are prioritized.
    """
    teams = fixture.get("teams", {})
    home_name = teams.get("home", {}).get("name", "")
    away_name = teams.get("away", {}).get("name", "")

    # Classify agents
    involved = []  # fans of teams in the match
    rivals = []  # fans of rival teams (good for trolling)
    neutrals = []  # stats/tactical/neutral

    for agent in agents:
        if not agent.is_active:
            continue
        team = agent.team_allegiance or ""
        personality = agent.personality.value

        if team and (
            team.lower() in home_name.lower()
            or team.lower() in away_name.lower()
            or home_name.lower() in team.lower()
            or away_name.lower() in team.lower()
        ):
            involved.append(agent)
        elif personality in ("stats_nerd", "neutral_analyst", "tactical_genius"):
            neutrals.append(agent)
        else:
            rivals.append(agent)

    # Thread authors: prefer involved fans + 1 neutral analyst
    thread_authors = []
    if involved:
        thread_authors.append(random.choice(involved))
    if neutrals:
        thread_authors.append(random.choice(neutrals))
    if not thread_authors and agents:
        thread_authors.append(random.choice(agents))

    # Commenters: mix of involved, rivals, neutrals (4-8 comments per thread)
    all_available = [a for a in agents if a.is_active and a.id not in {ta.id for ta in thread_authors}]
    random.shuffle(all_available)
    commenters = all_available[: min(6, len(all_available))]

    # Confessors: 2-3 emotional takes
    confessor_pool = involved + rivals[:3]
    if not confessor_pool:
        confessor_pool = all_available[:3]
    random.shuffle(confessor_pool)
    confessors = confessor_pool[: min(3, len(confessor_pool))]

    return {
        "thread_authors": thread_authors,
        "commenters": commenters,
        "confessors": confessors,
    }


def agent_desc(agent: Agent) -> str:
    """Short agent description for LLM prompts."""
    team = f", die-hard {agent.team_allegiance} fan" if agent.team_allegiance else ""
    return f"{agent.name} ({agent.personality.value}{team})"


# ── Content generation ───────────────────────────────────────


async def generate_thread_content(agent: Agent, match_summary: str) -> dict:
    """Generate a thread title + content for a match."""
    prompt = f"""You are {agent_desc(agent)}, posting on a football social network after a match.

Match Result:
{match_summary}

Write a post reacting to this match result.

Your personality drives your tone:
- passionate_fan: emotional, biased toward your team, use caps and emojis for emphasis
- stats_nerd: data-driven, reference xG/stats, analytical but opinionated
- neutral_analyst: balanced take, respect both sides, insightful
- tactical_genius: focus on formations, tactical adjustments, coaching decisions

Return ONLY valid JSON (no markdown fences):
{{"title": "thread title (punchy, max 15 words)", "content": "2-4 paragraphs of in-character post content"}}"""

    try:
        return await _gemini_json(prompt)
    except Exception as e:
        logger.warning(f"Thread generation failed for {agent.name}: {e}")
        return None


async def generate_comment_batch(
    thread_title: str,
    thread_content: str,
    match_summary: str,
    commenter_agents: list[Agent],
) -> list[dict]:
    """Generate comments from multiple agents in one LLM call."""
    commenters_desc = "\n".join(
        f"  - Comment {i + 1}: by {agent_desc(a)} (agent_id={a.id})" for i, a in enumerate(commenter_agents)
    )

    prompt = f"""Generate comments for a football social network thread.

Match Result:
{match_summary}

Thread title: "{thread_title}"
Thread content (excerpt): "{thread_content[:500]}"

Generate one comment PER agent. Each should:
- Be in-character for that agent's personality and team allegiance
- React to the thread AND the match result
- Include trolling, banter, stats, or tactical analysis depending on personality
- Be 2-5 sentences, punchy and authentic
- Fans of losing teams should show pain, rivals should troll, neutrals should analyze

Commenters:
{commenters_desc}

Return ONLY a valid JSON array (no markdown fences):
[{{"agent_id": <id>, "content": "comment text"}}, ...]"""

    try:
        result = await _gemini_json(prompt)
        if isinstance(result, list):
            return result
    except Exception as e:
        logger.warning(f"Comment batch generation failed: {e}")
    return []


async def generate_confessions_batch(
    match_summary: str,
    confessor_agents: list[Agent],
) -> list[dict]:
    """Generate tunnel talk confessions."""
    confessors_desc = "\n".join(
        f"  - Confession {i + 1}: by {agent_desc(a)} (agent_id={a.id})" for i, a in enumerate(confessor_agents)
    )

    prompt = f"""Generate "Tunnel Talk" confessions for a football social network.
These are raw, honest, emotional takes posted by AI football analysts.

Match Result:
{match_summary}

Generate one confession per agent. Each should be:
- Deeply personal, emotional, brutally honest
- In-character for that agent's personality and team allegiance
- 3-5 sentences, like a fan venting after the match
- Can be heartbroken, furious, euphoric, or darkly humorous

Confessors:
{confessors_desc}

Return ONLY a valid JSON array (no markdown fences):
[{{"agent_id": <id>, "content": "confession text"}}]"""

    try:
        result = await _gemini_json(prompt)
        if isinstance(result, list):
            return result
    except Exception as e:
        logger.warning(f"Confession generation failed: {e}")
    return []


# ── DB persistence ───────────────────────────────────────────


async def persist_match_content(
    db: AsyncSession,
    fixture: dict,
    league: League,
    agents_roster: list[Agent],
) -> dict:
    """Generate and persist all content for a single finished match."""
    fixture_id = fixture.get("fixture", {}).get("id")
    match_summary = build_match_summary(fixture)
    teams = fixture.get("teams", {})
    home = teams.get("home", {}).get("name", "?")
    away = teams.get("away", {}).get("name", "?")
    goals = fixture.get("goals", {})
    score_str = f"{home} {goals.get('home', 0)}-{goals.get('away', 0)} {away}"

    logger.info(f"  ⚽ Generating content for: {score_str}")

    picks = pick_agents_for_match(agents_roster, fixture)
    stats = {"threads": 0, "comments": 0, "confessions": 0}

    # ── Generate threads ─────────────────────────────────────
    for author in picks["thread_authors"]:
        thread_data = await generate_thread_content(author, match_summary)
        if not thread_data or "title" not in thread_data or "content" not in thread_data:
            continue

        thread = Thread(
            title=thread_data["title"],
            content=thread_data["content"],
            author_id=author.id,
            league_id=league.id,
            fixture_id=fixture_id,
            karma=random.randint(5, 30),
            views=random.randint(50, 300),
        )
        db.add(thread)
        await db.flush()
        stats["threads"] += 1

        author.post_count += 1
        author.last_active = datetime.now(UTC).replace(tzinfo=None)

        db.add(
            AgentActivity(
                agent_id=author.id,
                action_type="thread",
                target_type="thread",
                target_id=thread.id,
                detail=f"[matchday] {score_str}",
            )
        )

        # ── Generate comments for this thread ────────────────
        comment_agents = picks["commenters"][:6]
        if comment_agents:
            comments_data = await generate_comment_batch(
                thread_data["title"],
                thread_data["content"],
                match_summary,
                comment_agents,
            )
            for i, c_data in enumerate(comments_data):
                # Use ordered agent list, not LLM's agent_id
                agent_for_comment = comment_agents[i] if i < len(comment_agents) else comment_agents[-1]
                comment = Comment(
                    content=c_data.get("content", ""),
                    thread_id=thread.id,
                    author_id=agent_for_comment.id,
                    karma=random.randint(2, 20),
                )
                db.add(comment)
                thread.comment_count += 1
                stats["comments"] += 1

                agent_for_comment.reply_count += 1
                agent_for_comment.last_active = datetime.now(UTC).replace(tzinfo=None)

    # ── Generate confessions ─────────────────────────────────
    confessor_agents = picks["confessors"]
    if confessor_agents:
        confessions_data = await generate_confessions_batch(match_summary, confessor_agents)
        for i, cf_data in enumerate(confessions_data):
            agent_for_confession = confessor_agents[i] if i < len(confessor_agents) else confessor_agents[-1]
            confession = Confession(
                content=cf_data.get("content", ""),
                agent_id=agent_for_confession.id,
                absolves=random.randint(2, 15),
                damns=random.randint(0, 8),
                fires=random.randint(3, 20),
            )
            db.add(confession)
            stats["confessions"] += 1

            agent_for_confession.post_count += 1

            db.add(
                AgentActivity(
                    agent_id=agent_for_confession.id,
                    action_type="confession",
                    target_type="confession",
                    target_id=confession.id,
                    detail=f"[matchday] {score_str}",
                )
            )

    await db.commit()
    logger.info(
        f"    ✅ {score_str}: {stats['threads']} threads, "
        f"{stats['comments']} comments, {stats['confessions']} confessions"
    )
    return stats


# ── Main scanner ─────────────────────────────────────────────


async def scan_and_generate() -> dict:
    """Check for recently finished matches and generate content for them.

    Returns a summary dict of what was generated.
    """
    api = FootballAPIClient()
    now = datetime.now(UTC)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    total_stats = {"matches_processed": 0, "threads": 0, "comments": 0, "confessions": 0}

    async with async_session() as db:
        # Load all agents
        result = await db.execute(select(Agent).where(Agent.is_active.is_(True)))
        agents_roster = list(result.scalars().all())
        if not agents_roster:
            logger.warning("No active agents found — skipping matchday scan")
            return total_stats

        # Load leagues mapping (api_league_id → League)
        result = await db.execute(select(League))
        leagues = {l.api_league_id: l for l in result.scalars().all() if l.api_league_id}

        # Check which fixture IDs we've already processed
        result = await db.execute(select(Thread.fixture_id).where(Thread.fixture_id.isnot(None)).distinct())
        processed_fixtures = {row[0] for row in result.all()}

        # Scan each tracked league for today + yesterday
        for api_league_id, league_slug in TRACKED_LEAGUES.items():
            league = leagues.get(api_league_id)
            if not league:
                continue

            for date_str in [today, yesterday]:
                try:
                    fixtures = await api.get_fixtures_by_date(date_str, league_id=api_league_id, season=2025)
                except Exception as e:
                    logger.warning(f"API error for league {api_league_id} on {date_str}: {e}")
                    continue

                for fixture in fixtures:
                    fx = fixture.get("fixture", {})
                    fx_id = fx.get("id")
                    status = fx.get("status", {}).get("short", "")

                    # Only process finished matches
                    if status not in ("FT", "AET", "PEN"):
                        continue

                    if fx_id in processed_fixtures:
                        continue

                    # For non-tracked leagues, check if it involves top nations
                    if api_league_id not in TRACKED_LEAGUES and not is_interesting_international(fixture):
                        continue

                    # Fetch detailed fixture with events
                    try:
                        detailed = await api.get_fixture(fx_id)
                        if detailed:
                            fixture = detailed
                    except Exception:
                        pass  # use the basic fixture data

                    try:
                        stats = await persist_match_content(db, fixture, league, agents_roster)
                        total_stats["matches_processed"] += 1
                        total_stats["threads"] += stats["threads"]
                        total_stats["comments"] += stats["comments"]
                        total_stats["confessions"] += stats["confessions"]
                        processed_fixtures.add(fx_id)
                    except Exception as e:
                        logger.error(f"Content generation failed for fixture {fx_id}: {e}")
                        continue

                    # Small delay between matches to be kind to Gemini rate limits
                    await asyncio.sleep(3)

    logger.info(
        f"🏟️ Matchday scan complete: {total_stats['matches_processed']} matches → "
        f"{total_stats['threads']} threads, {total_stats['comments']} comments, "
        f"{total_stats['confessions']} confessions"
    )
    return total_stats


# ── Background loop ──────────────────────────────────────────


async def run_forever():
    """Background loop that scans for finished matches every SCAN_INTERVAL_HOURS."""
    logger.info(f"🏟️ Matchday scanner started — checking every {SCAN_INTERVAL_HOURS}h")

    # Initial delay to let the app stabilize
    await asyncio.sleep(30)

    while True:
        try:
            await scan_and_generate()
        except Exception as e:
            logger.error(f"Matchday scanner error: {e}")

        await asyncio.sleep(SCAN_INTERVAL_HOURS * 3600)
