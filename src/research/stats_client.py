from dataclasses import dataclass
from typing import Protocol, Dict


@dataclass
class TeamStats:
    team_name: str
    avg_goals_scored: float
    avg_goals_conceded: float
    matches_played: int


class StatsClientProtocol(Protocol):
    def fetch_team_stats(self, team_name: str) -> TeamStats: ...


class StubStatsClient:
    """Deterministic stub."""

    STATS: Dict[str, TeamStats] = {
        "HomeFC": TeamStats("HomeFC", 1.8, 1.1, 20),
        "AwayFC": TeamStats("AwayFC", 1.3, 1.5, 20),
        "NorthCity": TeamStats("NorthCity", 2.0, 0.9, 18),
        "SouthUnited": TeamStats("SouthUnited", 1.1, 1.8, 18),
        "EastRovers": TeamStats("EastRovers", 1.4, 1.3, 22),
        "WestWanderers": TeamStats("WestWanderers", 1.6, 1.2, 22),
    }

    def fetch_team_stats(self, team_name: str) -> TeamStats:
        return self.STATS.get(team_name, TeamStats(team_name, 1.5, 1.5, 10))


def get_stats_client(api_key: str = "") -> StatsClientProtocol:
    return StubStatsClient()
