"""
API-Football v3 comprehensive integration.
https://v3.football.api-sports.io

Covers: fixtures, standings, teams, players, leagues, predictions,
head-to-head, events, lineups, statistics, top scorers, injuries, transfers.
"""
import httpx
import logging
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class FootballAPIClient:
    """Full-featured client for API-Football v3."""

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        self.headers = {
            "x-apisports-key": settings.api_football_key
        }

    async def _request(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make GET request to API-Football."""
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.BASE_URL}/{endpoint}"
            logger.debug(f"API-Football → {url} params={params}")
            response = await client.get(url, headers=self.headers, params=params or {})
            response.raise_for_status()
            data = response.json()
            errors = data.get("errors", {})
            if errors:
                logger.warning(f"API-Football errors: {errors}")
            return data

    # ─── Status ──────────────────────────────────────────────────────
    async def get_status(self) -> dict:
        return await self._request("status")

    # ─── Fixtures ────────────────────────────────────────────────────
    async def get_live_fixtures(self, league_ids: str | None = None) -> list[dict]:
        params = {"live": league_ids or "all"}
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def get_fixtures_by_date(self, date_str: str, league_id: int | None = None,
                                    season: int | None = None, timezone: str = "Europe/London") -> list[dict]:
        params: dict[str, Any] = {"date": date_str, "timezone": timezone}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def get_fixture(self, fixture_id: int) -> dict | None:
        data = await self._request("fixtures", {"id": fixture_id})
        fixtures = data.get("response", [])
        return fixtures[0] if fixtures else None

    async def get_fixtures_by_ids(self, fixture_ids: list[int]) -> list[dict]:
        ids_str = "-".join(str(fid) for fid in fixture_ids[:20])
        data = await self._request("fixtures", {"ids": ids_str})
        return data.get("response", [])

    async def get_next_fixtures(self, team_id: int | None = None, league_id: int | None = None,
                                 count: int = 10) -> list[dict]:
        params: dict[str, Any] = {"next": min(count, 99)}
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def get_last_fixtures(self, team_id: int | None = None, league_id: int | None = None,
                                 count: int = 10) -> list[dict]:
        params: dict[str, Any] = {"last": min(count, 99)}
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def get_fixture_events(self, fixture_id: int, team_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id
        data = await self._request("fixtures/events", params)
        return data.get("response", [])

    async def get_fixture_lineups(self, fixture_id: int) -> list[dict]:
        data = await self._request("fixtures/lineups", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_fixture_statistics(self, fixture_id: int, team_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"fixture": fixture_id}
        if team_id:
            params["team"] = team_id
        data = await self._request("fixtures/statistics", params)
        return data.get("response", [])

    async def get_fixture_players(self, fixture_id: int) -> list[dict]:
        data = await self._request("fixtures/players", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_rounds(self, league_id: int, season: int, current: bool = False) -> list:
        params: dict[str, Any] = {"league": league_id, "season": season}
        if current:
            params["current"] = "true"
        data = await self._request("fixtures/rounds", params)
        return data.get("response", [])

    async def get_head_to_head(self, team1_id: int, team2_id: int, last: int = 10) -> list[dict]:
        data = await self._request("fixtures/headtohead", {
            "h2h": f"{team1_id}-{team2_id}", "last": last
        })
        return data.get("response", [])

    # ─── Standings ───────────────────────────────────────────────────
    async def get_standings(self, league_id: int, season: int, team_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"league": league_id, "season": season}
        if team_id:
            params["team"] = team_id
        data = await self._request("standings", params)
        response = data.get("response", [])
        if response:
            standings_data = response[0].get("league", {}).get("standings", [[]])
            return standings_data[0] if standings_data else []
        return []

    # ─── Teams ───────────────────────────────────────────────────────
    async def get_team(self, team_id: int) -> dict | None:
        data = await self._request("teams", {"id": team_id})
        teams = data.get("response", [])
        return teams[0] if teams else None

    async def get_teams_by_league(self, league_id: int, season: int) -> list[dict]:
        data = await self._request("teams", {"league": league_id, "season": season})
        return data.get("response", [])

    async def search_teams(self, name: str) -> list[dict]:
        if len(name) < 3:
            return []
        data = await self._request("teams", {"search": name})
        return data.get("response", [])

    async def get_team_stats(self, team_id: int, league_id: int, season: int) -> dict | None:
        data = await self._request("teams/statistics", {
            "team": team_id, "league": league_id, "season": season
        })
        return data.get("response")

    # ─── Leagues ─────────────────────────────────────────────────────
    async def get_leagues(self, country: str | None = None, season: int | None = None,
                          current: bool = False, search: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if country:
            params["country"] = country
        if season:
            params["season"] = season
        if current:
            params["current"] = "true"
        if search:
            params["search"] = search
        data = await self._request("leagues", params)
        return data.get("response", [])

    async def get_league(self, league_id: int) -> dict | None:
        data = await self._request("leagues", {"id": league_id})
        leagues = data.get("response", [])
        return leagues[0] if leagues else None

    async def get_seasons(self) -> list[int]:
        data = await self._request("leagues/seasons")
        return data.get("response", [])

    # ─── Players ─────────────────────────────────────────────────────
    async def get_player_stats(self, player_id: int, season: int) -> dict | None:
        data = await self._request("players", {"id": player_id, "season": season})
        players = data.get("response", [])
        return players[0] if players else None

    async def get_squad(self, team_id: int) -> list[dict]:
        data = await self._request("players/squads", {"team": team_id})
        response = data.get("response", [])
        if response:
            return response[0].get("players", [])
        return []

    async def get_top_scorers(self, league_id: int, season: int) -> list[dict]:
        data = await self._request("players/topscorers", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_top_assists(self, league_id: int, season: int) -> list[dict]:
        data = await self._request("players/topassists", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_top_yellow_cards(self, league_id: int, season: int) -> list[dict]:
        data = await self._request("players/topyellowcards", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_top_red_cards(self, league_id: int, season: int) -> list[dict]:
        data = await self._request("players/topredcards", {"league": league_id, "season": season})
        return data.get("response", [])

    # ─── Predictions ─────────────────────────────────────────────────
    async def get_predictions(self, fixture_id: int) -> dict | None:
        data = await self._request("predictions", {"fixture": fixture_id})
        predictions = data.get("response", [])
        return predictions[0] if predictions else None

    # ─── Injuries ────────────────────────────────────────────────────
    async def get_injuries(self, fixture_id: int | None = None, league_id: int | None = None,
                            season: int | None = None, team_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if fixture_id:
            params["fixture"] = fixture_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if team_id:
            params["team"] = team_id
        data = await self._request("injuries", params)
        return data.get("response", [])

    # ─── Transfers ───────────────────────────────────────────────────
    async def get_transfers(self, player_id: int | None = None, team_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if player_id:
            params["player"] = player_id
        if team_id:
            params["team"] = team_id
        data = await self._request("transfers", params)
        return data.get("response", [])

    # ─── Coaches ─────────────────────────────────────────────────────
    async def get_coach(self, team_id: int | None = None, coach_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if team_id:
            params["team"] = team_id
        if coach_id:
            params["id"] = coach_id
        data = await self._request("coachs", params)
        return data.get("response", [])

    # ─── Countries ───────────────────────────────────────────────────
    async def get_countries(self) -> list[dict]:
        data = await self._request("countries")
        return data.get("response", [])

    # ─── Venues ──────────────────────────────────────────────────────
    async def get_venue(self, venue_id: int) -> dict | None:
        data = await self._request("venues", {"id": venue_id})
        venues = data.get("response", [])
        return venues[0] if venues else None

    # ─── Trophies ────────────────────────────────────────────────────
    async def get_trophies(self, player_id: int | None = None, coach_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if player_id:
            params["player"] = player_id
        if coach_id:
            params["coach"] = coach_id
        data = await self._request("trophies", params)
        return data.get("response", [])

    # ─── Odds ────────────────────────────────────────────────────────
    async def get_odds(self, fixture_id: int, bookmaker_id: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"fixture": fixture_id}
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        data = await self._request("odds", params)
        return data.get("response", [])


# Singleton
football_api = FootballAPIClient()
