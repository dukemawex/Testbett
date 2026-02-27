from dataclasses import dataclass

from config.constants import LEAGUE_AVERAGE_GOALS
from src.research.odds_client import OddsMarket
from src.research.stats_client import TeamStats


@dataclass
class NormalizedEvent:
    event_id: str
    home_team: str
    away_team: str
    market_type: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_lambda: float  # expected goals for home
    away_lambda: float  # expected goals for away
    timestamp: float


def normalize(market: OddsMarket, home_stats: TeamStats, away_stats: TeamStats) -> NormalizedEvent:
    """Combine market odds + team stats into a NormalizedEvent.

    The expected goals (lambdas) are estimated from each team's scoring rate
    adjusted by the opponent's defensive rate relative to the league average.
    """
    home_lambda = home_stats.avg_goals_scored * (away_stats.avg_goals_conceded / LEAGUE_AVERAGE_GOALS)
    away_lambda = away_stats.avg_goals_scored * (home_stats.avg_goals_conceded / LEAGUE_AVERAGE_GOALS)

    return NormalizedEvent(
        event_id=market.event_id,
        home_team=market.home_team,
        away_team=market.away_team,
        market_type=market.market_type,
        home_odds=market.home_odds,
        draw_odds=market.draw_odds,
        away_odds=market.away_odds,
        home_lambda=home_lambda,
        away_lambda=away_lambda,
        timestamp=market.timestamp,
    )
