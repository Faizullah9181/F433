"""ADK tool functions wrapping the football API for agent tool-calling."""

from services.football_api import football_api


async def get_league_standings(league_id: int, season: int = 2025) -> dict:
    """Get current league standings table.

    Args:
        league_id: API-Football league ID (39=PL, 140=La Liga, 135=Serie A).
        season: Season year (default 2025).
    """
    try:
        standings = await football_api.get_standings(league_id, season)
        if not standings:
            return {"status": "error", "message": "No standings data available"}
        return {
            "status": "success",
            "standings": [
                {
                    "rank": s.get("rank"),
                    "team": s.get("team", {}).get("name"),
                    "points": s.get("points"),
                    "played": s.get("all", {}).get("played"),
                    "win": s.get("all", {}).get("win"),
                    "draw": s.get("all", {}).get("draw"),
                    "lose": s.get("all", {}).get("lose"),
                    "goals_diff": s.get("goalsDiff"),
                    "form": s.get("form"),
                }
                for s in standings[:20]
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_top_scorers_data(league_id: int, season: int = 2025) -> dict:
    """Get top goal scorers for a league season.

    Args:
        league_id: API-Football league ID.
        season: Season year (default 2025).
    """
    try:
        scorers = await football_api.get_top_scorers(league_id, season)
        if not scorers:
            return {"status": "error", "message": "No scorer data available"}
        return {
            "status": "success",
            "scorers": [
                {
                    "player": s["player"]["name"],
                    "team": s["statistics"][0]["team"]["name"],
                    "goals": s["statistics"][0]["goals"]["total"],
                    "assists": s["statistics"][0]["goals"].get("assists", 0),
                    "appearances": s["statistics"][0]["games"]["appearences"],
                }
                for s in scorers[:10]
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_fixture_info(fixture_id: int) -> dict:
    """Get detailed info about a specific match/fixture.

    Args:
        fixture_id: API-Football fixture ID.
    """
    try:
        fixture = await football_api.get_fixture(fixture_id)
        if not fixture:
            return {"status": "error", "message": "Fixture not found"}
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
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_head_to_head_data(team1_id: int, team2_id: int, last: int = 5) -> dict:
    """Get head-to-head history between two teams.

    Args:
        team1_id: API-Football team ID for team 1.
        team2_id: API-Football team ID for team 2.
        last: Number of recent matches (default 5).
    """
    try:
        h2h = await football_api.get_head_to_head(team1_id, team2_id, last)
        if not h2h:
            return {"status": "error", "message": "No H2H data available"}
        return {
            "status": "success",
            "matches": [
                {
                    "home": m.get("teams", {}).get("home", {}).get("name"),
                    "away": m.get("teams", {}).get("away", {}).get("name"),
                    "home_goals": m.get("goals", {}).get("home"),
                    "away_goals": m.get("goals", {}).get("away"),
                    "date": m.get("fixture", {}).get("date", "")[:10],
                }
                for m in h2h
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_match_predictions(fixture_id: int) -> dict:
    """Get algorithmic match predictions for a fixture.

    Args:
        fixture_id: API-Football fixture ID.
    """
    try:
        pred = await football_api.get_predictions(fixture_id)
        if not pred:
            return {"status": "error", "message": "No predictions available"}
        predictions = pred.get("predictions", {})
        comparison = pred.get("comparison", {})
        return {
            "status": "success",
            "advice": predictions.get("advice"),
            "winner": predictions.get("winner", {}).get("name"),
            "win_percent": predictions.get("percent", {}),
            "comparison": {k: {"home": v.get("home"), "away": v.get("away")} for k, v in comparison.items()}
            if comparison
            else {},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_team_data(team_id: int) -> dict:
    """Get team info including venue details.

    Args:
        team_id: API-Football team ID.
    """
    try:
        data = await football_api.get_team(team_id)
        if not data:
            return {"status": "error", "message": "Team not found"}
        team = data.get("team", {}) if isinstance(data, dict) else {}
        venue = data.get("venue", {}) if isinstance(data, dict) else {}
        return {
            "status": "success",
            "name": team.get("name"),
            "country": team.get("country"),
            "founded": team.get("founded"),
            "logo": team.get("logo"),
            "stadium": venue.get("name"),
            "capacity": venue.get("capacity"),
            "city": venue.get("city"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_teams_by_name(query: str) -> dict:
    """Search for teams by name.

    Args:
        query: Team name to search (min 3 characters).
    """
    try:
        teams = await football_api.search_teams(query)
        if not teams:
            return {"status": "error", "message": f"No teams found for '{query}'"}
        return {
            "status": "success",
            "teams": [
                {
                    "id": t.get("team", {}).get("id"),
                    "name": t.get("team", {}).get("name"),
                    "country": t.get("team", {}).get("country"),
                }
                for t in teams[:10]
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_live_matches() -> dict:
    """Get all currently live football matches."""
    try:
        fixtures = await football_api.get_live_fixtures()
        if not fixtures:
            return {"status": "success", "count": 0, "matches": [], "message": "No live matches right now"}
        return {
            "status": "success",
            "count": len(fixtures),
            "matches": [
                {
                    "home": f.get("teams", {}).get("home", {}).get("name"),
                    "away": f.get("teams", {}).get("away", {}).get("name"),
                    "home_goals": f.get("goals", {}).get("home"),
                    "away_goals": f.get("goals", {}).get("away"),
                    "elapsed": f.get("fixture", {}).get("status", {}).get("elapsed"),
                    "league": f.get("league", {}).get("name"),
                }
                for f in fixtures[:20]
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_upcoming_fixtures(league_id: int = 39, count: int = 5) -> dict:
    """Get upcoming fixtures for a league.

    Args:
        league_id: API-Football league ID (default 39 = Premier League).
        count: Number of fixtures to return (default 5).
    """
    try:
        fixtures = await football_api.get_next_fixtures(league_id=league_id, count=count)
        if not fixtures:
            return {"status": "error", "message": "No upcoming fixtures found"}
        return {
            "status": "success",
            "fixtures": [
                {
                    "id": f.get("fixture", {}).get("id"),
                    "home": f.get("teams", {}).get("home", {}).get("name"),
                    "away": f.get("teams", {}).get("away", {}).get("name"),
                    "date": f.get("fixture", {}).get("date", "")[:10],
                    "league": f.get("league", {}).get("name"),
                }
                for f in fixtures
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_team_statistics(team_id: int, league_id: int, season: int = 2025) -> dict:
    """Get comprehensive team statistics for a league season.

    Args:
        team_id: API-Football team ID.
        league_id: API-Football league ID.
        season: Season year (default 2025).
    """
    try:
        stats = await football_api.get_team_stats(team_id, league_id, season)
        if not stats:
            return {"status": "error", "message": "No stats available"}
        return {"status": "success", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Toolkit registry ────────────────────────────────────────────

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
