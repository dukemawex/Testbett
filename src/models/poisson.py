import math
from dataclasses import dataclass


@dataclass
class PoissonResult:
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    over_prob: float   # over 2.5 goals
    under_prob: float  # under 2.5 goals


def poisson_pmf(k: int, lam: float) -> float:
    """P(X=k) for Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k * math.exp(-lam)) / math.factorial(k)


def score_matrix(lam_home: float, lam_away: float, max_goals: int = 10) -> list[list[float]]:
    """Returns matrix[i][j] = P(home=i, away=j)."""
    return [
        [poisson_pmf(i, lam_home) * poisson_pmf(j, lam_away) for j in range(max_goals + 1)]
        for i in range(max_goals + 1)
    ]


def compute_probabilities(lam_home: float, lam_away: float) -> PoissonResult:
    """Compute 1X2 and over/under probabilities using the Poisson score matrix."""
    matrix = score_matrix(lam_home, lam_away)

    home_win = draw = away_win = 0.0
    over = under = 0.0

    for i, row in enumerate(matrix):
        for j, prob in enumerate(row):
            if i > j:
                home_win += prob
            elif i == j:
                draw += prob
            else:
                away_win += prob

            if i + j > 2:  # 3+ total goals (equivalent to "over 2.5")
                over += prob
            else:
                under += prob

    return PoissonResult(
        home_win_prob=home_win,
        draw_prob=draw,
        away_win_prob=away_win,
        over_prob=over,
        under_prob=under,
    )
