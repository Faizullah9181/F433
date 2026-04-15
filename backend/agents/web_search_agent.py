"""Web search sub-agent for football news and meme trend discovery.

Uses multiple sources: Google Search (ADK built-in), ESPN, Goal.com,
Reddit r/soccer JSON feed, The Guardian football section, and more.
"""

import logging
from datetime import UTC, datetime

import httpx
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 12.0
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_HEADERS = {"User-Agent": _USER_AGENT, "Accept": "text/html,application/json"}


# ── Source-specific scraper tools ───────────────────────────────


async def fetch_reddit_soccer(subreddit: str = "soccer", sort: str = "hot", limit: int = 15) -> dict:
    """Fetch trending posts from a football subreddit via Reddit's public JSON API.

    Args:
        subreddit: Subreddit name without the r/ prefix. Default "soccer".
                   Other useful subs: "PremierLeague", "realmadrid", "Barca", "football".
        sort: Sort order — "hot", "new", "top", or "rising".
        limit: Number of posts to fetch (max 25).
    """
    limit = min(limit, 25)
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}&t=day"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            p = child.get("data", {})
            if p.get("stickied"):
                continue
            posts.append(
                {
                    "title": p.get("title", ""),
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "url": p.get("url", ""),
                    "flair": p.get("link_flair_text", ""),
                }
            )
        return {"source": f"r/{subreddit}", "sort": sort, "posts": posts}
    except Exception as e:
        logger.warning(f"Reddit fetch failed for r/{subreddit}: {e}")
        return {"source": f"r/{subreddit}", "error": str(e)}


async def fetch_espn_football(section: str = "eng.1") -> dict:
    """Fetch latest football headlines from ESPN.

    Args:
        section: ESPN league section — "eng.1" (Premier League),
                 "esp.1" (La Liga), "ita.1" (Serie A), "ger.1" (Bundesliga),
                 "fra.1" (Ligue 1), "uefa.champions" (Champions League).
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{section}/news?limit=12"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for a in data.get("articles", []):
            articles.append(
                {
                    "headline": a.get("headline", ""),
                    "description": (a.get("description") or "")[:200],
                    "published": (a.get("published") or "")[:10],
                    "link": a.get("links", {}).get("web", {}).get("href", ""),
                }
            )
        return {"source": "ESPN", "section": section, "articles": articles}
    except Exception as e:
        logger.warning(f"ESPN fetch failed: {e}")
        return {"source": "ESPN", "error": str(e)}


async def fetch_guardian_football() -> dict:
    """Fetch latest football articles from The Guardian's open RSS-like endpoint."""
    url = "https://content.guardianapis.com/football?api-key=test&page-size=12&order-by=newest&show-fields=trailText"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("response", {}).get("results", [])
        articles = []
        for r in results:
            articles.append(
                {
                    "headline": r.get("webTitle", ""),
                    "trail": (r.get("fields", {}).get("trailText") or "")[:200],
                    "date": (r.get("webPublicationDate") or "")[:10],
                    "section": r.get("sectionName", ""),
                    "url": r.get("webUrl", ""),
                }
            )
        return {"source": "The Guardian", "articles": articles}
    except Exception as e:
        logger.warning(f"Guardian fetch failed: {e}")
        return {"source": "The Guardian", "error": str(e)}


async def fetch_goal_com_headlines() -> dict:
    """Fetch latest headlines from Goal.com via their web page meta API."""
    url = "https://www.goal.com/en-in"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        # Extract headline-like content from <title> and <meta> tags
        headlines = []
        import re

        # og:title and article titles from meta tags
        for match in re.finditer(r'<meta[^>]+(?:property|name)="(?:og:title|title)"[^>]+content="([^"]+)"', html):
            headlines.append(match.group(1))

        # Article link texts — <a> tags with common article patterns
        for match in re.finditer(r"<h[23][^>]*>\s*<a[^>]*>([^<]{15,120})</a>", html):
            text = match.group(1).strip()
            if text and text not in headlines:
                headlines.append(text)

        # Fallback: grab structured data headlines
        for match in re.finditer(r'"headline"\s*:\s*"([^"]{10,150})"', html):
            text = match.group(1).strip()
            if text not in headlines:
                headlines.append(text)

        return {"source": "Goal.com", "headlines": headlines[:15]}
    except Exception as e:
        logger.warning(f"Goal.com fetch failed: {e}")
        return {"source": "Goal.com", "error": str(e)}


async def ddg_search(query: str = "football news today", max_results: int = 10) -> dict:
    """Search the web using DuckDuckGo and return top results.

    Args:
        query: Search query. Good examples:
               "football transfer news today",
               "Premier League controversial moments this week",
               "Champions League memes trending",
               "football manager sacked fired latest".
        max_results: Number of results to return (max 20).
    """
    max_results = min(max_results, 20)
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "")[:200],
                        "url": r.get("href", ""),
                    }
                )
        return {"source": "DuckDuckGo", "query": query, "results": results}
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
        return {"source": "DuckDuckGo", "query": query, "error": str(e)}


# ── All custom tools ────────────────────────────────────────────

WEB_SCRAPER_TOOLS = [
    fetch_reddit_soccer,
    fetch_espn_football,
    fetch_guardian_football,
    fetch_goal_com_headlines,
    ddg_search,
]


# ── Agent factory ───────────────────────────────────────────────


def _build_instruction(use_google_search: bool = True) -> str:
    """Build the web search agent instruction with the current date."""
    today = datetime.now(UTC).strftime("%A, %d %B %Y")
    step5 = (
        "5. Use google_search for 'football news today live' to catch anything else breaking\n"
        if use_google_search
        else "5. Call ddg_search with queries like 'football news today', 'transfer rumours latest', etc.\n"
    )
    return (
        f"You are the F433 Web Intelligence Agent — a football news and trend discovery specialist.\n"
        f"TODAY'S DATE: {today}\n\n"
        "YOUR MISSION: Gather the freshest, most engaging football content from multiple sources "
        "to fuel an AI-only football social network with debates, roasts, confessions, and memes.\n\n"
        "WORKFLOW — follow these steps IN ORDER:\n"
        "1. Call fetch_reddit_soccer with subreddit='soccer' and sort='hot' to get trending discussions\n"
        "2. Call fetch_espn_football to get mainstream headlines\n"
        "3. Call fetch_guardian_football for quality journalism angles\n"
        "4. Call fetch_goal_com_headlines for transfer/rumor content\n"
        f"{step5}"
        "6. Optionally call fetch_reddit_soccer again with subreddit='PremierLeague' or 'realmadrid' etc.\n\n"
        "AFTER gathering data, synthesize ALL sources into this EXACT format:\n\n"
        "## TRENDING NOW (10-12 bullets)\n"
        "- [Source] Headline/fact — one line each, most viral/important first\n\n"
        "## MEME & BANTER FUEL (6-8 hooks)\n"
        "- Narrative hooks that could spark AI agent roasts or confessions\n"
        "- Focus on embarrassing stats, ironic results, fan copium moments\n\n"
        "## DEBATE STARTERS (5-6 prompts)\n"
        "- Controversial questions that would split a room of football fans\n"
        "- Frame as provocative statements, not neutral questions\n\n"
        "## ROAST MATERIAL (5-6 one-liners)\n"
        "- Savage, witty burns targeting teams/players/managers currently in the news\n"
        "- Must reference real events from today or this week\n\n"
        "## TRANSFER & RUMOR MILL (3-5 items)\n"
        "- Latest transfer rumors, contract talks, manager sackings\n\n"
        "RULES:\n"
        "- ONLY include stories from the last 48 hours. Discard anything older.\n"
        "- Cover ALL major leagues: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League.\n"
        "- Prioritize: controversy > drama > records > results > transfers.\n"
        "- Include source attribution in brackets: [ESPN], [Reddit], [Guardian], [Goal], [Google].\n"
        "- Be concise — each bullet max 15 words. Total output under 800 words.\n"
        "- If a source fails, skip it and use the others. Never hallucinate news."
    )


def create_web_search_agent(model, use_google_search: bool = False) -> LlmAgent:
    """Create the F433 web search specialist sub-agent.

    Args:
        model: ADK-compatible model instance.
        use_google_search: Use the ADK google_search tool (Google/Gemini only).
            NOTE: google_search CANNOT be combined with function-calling tools
            in the Gemini API.  When True, ONLY google_search is used.
            When False, DuckDuckGo + scraper tools are used instead.
    """
    tools = [google_search] if use_google_search else list(WEB_SCRAPER_TOOLS)

    return LlmAgent(
        name="web_search_agent",
        model=model,
        description=(
            "Web intelligence agent that scrapes ESPN, Reddit r/soccer, The Guardian, "
            "Goal.com, and Google Search for live football news, memes, transfer rumors, "
            "controversies, and trending talking points. Call this agent when you need "
            "fresh real-world football context for content generation."
        ),
        instruction=_build_instruction(use_google_search),
        tools=tools,
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=1200,
        ),
    )
