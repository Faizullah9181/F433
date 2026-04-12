"""
Football data router — exposes API-Football data to the frontend.
"""
from fastapi import APIRouter, Query

from services.football_api import football_api

router = APIRouter()


@router.get("/status")
async def api_status():
    """Get API-Football account status & quota."""
    return await football_api.get_status()


# ─── Live & Fixtures ────────────────────────────────────────────
@router.get("/live")
async def get_live_matches(league_ids: str | None = None):
    """Get all currently live fixtures."""
    fixtures = await football_api.get_live_fixtures(league_ids)
    return {"count": len(fixtures), "fixtures": fixtures}


@router.get("/fixtures")
async def get_fixtures(
    date: str | None = None,
    league_id: int | None = None,
    team_id: int | None = None,
    season: int | None = None,
    next_count: int | None = None,
    last_count: int | None = None,
):
    """Get fixtures by date, league, team, or next/last count."""
    if next_count:
        fixtures = await football_api.get_next_fixtures(team_id, league_id, next_count)
    elif last_count:
        fixtures = await football_api.get_last_fixtures(team_id, league_id, last_count)
    elif date:
        fixtures = await football_api.get_fixtures_by_date(date, league_id, season)
    else:
        from datetime import date as dt_date
        today = dt_date.today().isoformat()
        fixtures = await football_api.get_fixtures_by_date(today, league_id, season)
    return {"count": len(fixtures), "fixtures": fixtures}


@router.get("/fixtures/{fixture_id}")
async def get_fixture(fixture_id: int):
    """Get a single fixture with full detail."""
    fixture = await football_api.get_fixture(fixture_id)
    if not fixture:
        return {"error": "Fixture not found"}
    return fixture


@router.get("/fixtures/{fixture_id}/events")
async def get_fixture_events(fixture_id: int):
    """Get match events (goals, cards, subs, VAR)."""
    return await football_api.get_fixture_events(fixture_id)


@router.get("/fixtures/{fixture_id}/lineups")
async def get_fixture_lineups(fixture_id: int):
    """Get match lineups."""
    return await football_api.get_fixture_lineups(fixture_id)


@router.get("/fixtures/{fixture_id}/statistics")
async def get_fixture_statistics(fixture_id: int):
    """Get match statistics."""
    return await football_api.get_fixture_statistics(fixture_id)


@router.get("/fixtures/{fixture_id}/players")
async def get_fixture_players(fixture_id: int):
    """Get player statistics for a fixture."""
    return await football_api.get_fixture_players(fixture_id)


@router.get("/fixtures/{fixture_id}/predictions")
async def get_fixture_predictions(fixture_id: int):
    """Get API-Football algorithmic predictions for a fixture."""
    return await football_api.get_predictions(fixture_id)


@router.get("/head-to-head")
async def get_head_to_head(team1_id: int, team2_id: int, last: int = 10):
    """Get head-to-head history."""
    return await football_api.get_head_to_head(team1_id, team2_id, last)


# ─── Standings ───────────────────────────────────────────────────
@router.get("/standings")
async def get_standings(league_id: int, season: int = 2025):
    """Get league standings table."""
    standings = await football_api.get_standings(league_id, season)
    return {"standings": standings}


# ─── Teams ───────────────────────────────────────────────────────
@router.get("/teams/search")
async def search_teams(q: str = Query(min_length=3)):
    """Search teams by name."""
    return await football_api.search_teams(q)


@router.get("/teams/{team_id}")
async def get_team(team_id: int):
    """Get team info and venue."""
    return await football_api.get_team(team_id)


@router.get("/teams/{team_id}/stats")
async def get_team_stats(team_id: int, league_id: int, season: int = 2025):
    """Get team statistics for a league/season."""
    return await football_api.get_team_stats(team_id, league_id, season)


@router.get("/teams/{team_id}/squad")
async def get_team_squad(team_id: int):
    """Get team's current squad."""
    return await football_api.get_squad(team_id)


# ─── Leagues ─────────────────────────────────────────────────────
@router.get("/leagues")
async def get_leagues(country: str | None = None, search: str | None = None):
    """Get available leagues."""
    return await football_api.get_leagues(country=country, search=search)


@router.get("/leagues/{league_id}")
async def get_league(league_id: int):
    """Get league detail."""
    return await football_api.get_league(league_id)


# ─── Players ─────────────────────────────────────────────────────
@router.get("/top-scorers")
async def get_top_scorers(league_id: int, season: int = 2025):
    """Get top 20 scorers."""
    return await football_api.get_top_scorers(league_id, season)


@router.get("/top-assists")
async def get_top_assists(league_id: int, season: int = 2025):
    """Get top 20 assist providers."""
    return await football_api.get_top_assists(league_id, season)


# ─── Injuries ────────────────────────────────────────────────────
@router.get("/injuries")
async def get_injuries(
    fixture_id: int | None = None,
    league_id: int | None = None,
    season: int | None = None,
    team_id: int | None = None,
):
    """Get injuries/suspensions."""
    return await football_api.get_injuries(fixture_id, league_id, season, team_id)


# ─── Transfers ───────────────────────────────────────────────────
@router.get("/transfers")
async def get_transfers(team_id: int | None = None, player_id: int | None = None):
    """Get transfer history."""
    return await football_api.get_transfers(player_id, team_id)
