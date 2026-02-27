from dataclasses import dataclass
from src.models.poisson import PoissonResult


@dataclass
class MarketProbabilities:
    home_win: float
    draw: float
    away_win: float
    over_25: float
    under_25: float


def compute_true_probabilities(poisson_result: PoissonResult) -> MarketProbabilities:
    """Extract true probabilities from Poisson result."""
    return MarketProbabilities(
        home_win=poisson_result.home_win_prob,
        draw=poisson_result.draw_prob,
        away_win=poisson_result.away_win_prob,
        over_25=poisson_result.over_prob,
        under_25=poisson_result.under_prob,
    )


def implied_probability(decimal_odds: float) -> float:
    """Implied probability from decimal odds: 1/odds."""
    if decimal_odds <= 0:
        raise ValueError("Odds must be positive")
    return 1.0 / decimal_odds


def devig(home_odds: float, draw_odds: float, away_odds: float) -> tuple[float, float, float]:
    """Remove vig using proportional method. Returns fair probabilities summing to 1.0."""
    raw = [implied_probability(o) for o in [home_odds, draw_odds, away_odds]]
    total = sum(raw)
    return tuple(p / total for p in raw)  # type: ignore[return-value]


def compute_edge(true_prob: float, decimal_odds: float) -> float:
    """Edge = true_prob - implied_prob."""
    return true_prob - implied_probability(decimal_odds)
