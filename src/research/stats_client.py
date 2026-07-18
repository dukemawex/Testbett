from dataclasses import dataclass
from typing import Protocol, Dict, Optional
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


@dataclass
class TeamStats:
    team_name: str
    avg_goals_scored: float
    avg_goals_conceded: float
    matches_played: int
    is_real: bool = False  # True only when derived from real match data


class StatsClientProtocol(Protocol):
    def fetch_team_stats(self, team_name: str) -> TeamStats: ...


class StubStatsClient:
    """Deterministic stub for offline/dev. Marked is_real=False so callers can refuse to bet on it."""

    STATS: Dict[str, TeamStats] = {
        "HomeFC": TeamStats("HomeFC", 1.8, 1.1, 20),
        "AwayFC": TeamStats("AwayFC", 1.3, 1.5, 20),
        "NorthCity": TeamStats("NorthCity", 2.0, 0.9, 18),
        "SouthUnited": TeamStats("SouthUnited", 1.1, 1.8, 18),
        "EastRovers": TeamStats("EastRovers", 1.4, 1.3, 22),
        "WestWanderers": TeamStats("WestWanderers", 1.6, 1.2, 22),
    }

    def fetch_team_stats(self, team_name: str) -> TeamStats:
        s = self.STATS.get(team_name)
        if s:
            return s
        # Unknown team -> uniform default, explicitly NOT real.
        return TeamStats(team_name, 1.5, 1.5, 10, is_real=False)


class FootballDataStatsClient:
    """Real team stats from football-data.org (free tier).

    Derives each team's average goals scored/conceded from recent FINISHED matches
    in a competition. Requires FOOTBALL_DATA_API_KEY. Results are cached per run to
    respect the free-tier rate limit (competition standings/matches fetched once).

    competition: football-data.org code, e.g. "PL" (Premier League), "PD" (La Liga),
    "SA" (Serie A), "BL1" (Bundesliga), "FL1" (Ligue 1).
    """

    _BASE = "https://api.football-data.org/v4"
    _TIMEOUT = 15

    def __init__(self, api_key: str, competition: str = "PL", lookback: int = 10):
        self._key = api_key
        self._competition = competition
        self._lookback = lookback
        self._cache: Dict[str, TeamStats] = {}
        self._loaded = False

    def _get(self, path: str) -> Optional[dict]:
        url = f"{self._BASE}{path}"
        req = urllib.request.Request(url, headers={"X-Auth-Token": self._key})
        try:
            with urllib.request.urlopen(req, timeout=self._TIMEOUT) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            logger.warning("football-data HTTP %s for %s", exc.code, path)
        except Exception as exc:
            logger.warning("football-data fetch failed for %s: %s", path, exc)
        return None

    def _load(self) -> None:
        """Fetch finished matches once and build per-team scored/conceded averages."""
        self._loaded = True
        data = self._get(f"/competitions/{self._competition}/matches?status=FINISHED")
        if not data or "matches" not in data:
            logger.warning("football-data: no finished matches for %s; stats unavailable", self._competition)
            return

        agg: Dict[str, list] = {}  # team -> [scored_total, conceded_total, games]
        for m in data["matches"]:
            ft = (m.get("score") or {}).get("fullTime") or {}
            hs, as_ = ft.get("home"), ft.get("away")
            if hs is None or as_ is None:
                continue
            home = (m.get("homeTeam") or {}).get("name")
            away = (m.get("awayTeam") or {}).get("name")
            if not home or not away:
                continue
            agg.setdefault(home, [0, 0, 0])
            agg.setdefault(away, [0, 0, 0])
            agg[home][0] += hs; agg[home][1] += as_; agg[home][2] += 1
            agg[away][0] += as_; agg[away][1] += hs; agg[away][2] += 1

        for team, (scored, conceded, games) in agg.items():
            if games == 0:
                continue
            self._cache[team] = TeamStats(
                team_name=team,
                avg_goals_scored=round(scored / games, 4),
                avg_goals_conceded=round(conceded / games, 4),
                matches_played=games,
                is_real=True,
            )
        logger.info("football-data: built real stats for %d teams in %s", len(self._cache), self._competition)

    def fetch_team_stats(self, team_name: str) -> TeamStats:
        if not self._loaded:
            self._load()
        s = self._cache.get(team_name)
        if s:
            return s
        # try a loose match (Odds API names differ slightly from football-data names)
        for name, stats in self._cache.items():
            if _name_matches(team_name, name):
                return stats
        logger.warning("football-data: no real stats for '%s'; returning non-real default", team_name)
        return TeamStats(team_name, 1.5, 1.5, 0, is_real=False)


def _name_matches(a: str, b: str) -> bool:
    """Loose team-name match across data sources (e.g. 'Man United' vs 'Manchester United FC')."""
    def norm(x: str) -> set:
        drop = {"fc", "afc", "and", "hove", "albion", "city", "united", "the"}
        toks = {t for t in x.lower().replace("&", " ").replace(".", " ").split() if t not in drop}
        return toks
    ta, tb = norm(a), norm(b)
    if not ta or not tb:
        return False
    return len(ta & tb) >= 1 and (ta <= tb or tb <= ta or len(ta & tb) >= 2)


def get_stats_client(api_key: str = "", competition: str = "PL") -> StatsClientProtocol:
    """Return the real football-data client when a key is set, else the stub."""
    if api_key:
        return FootballDataStatsClient(api_key, competition=competition)
    return StubStatsClient()
