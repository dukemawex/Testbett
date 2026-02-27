def kelly_fraction(true_prob: float, decimal_odds: float) -> float:
    """Kelly Criterion: f = (b*p - q) / b.

    Where:
        b = decimal_odds - 1  (net profit per unit stake)
        p = true_prob
        q = 1 - p

    Returns the fraction of bankroll to wager, clamped to [0, 1].
    A negative Kelly (negative edge) is clamped to 0 – no bet.
    """
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - true_prob
    f = (b * true_prob - q) / b
    return max(0.0, min(1.0, f))


def fractional_kelly(true_prob: float, decimal_odds: float, fraction: float = 0.25) -> float:
    """Apply fractional Kelly multiplier to reduce variance."""
    return fraction * kelly_fraction(true_prob, decimal_odds)


def compute_stake(
    bankroll: float,
    true_prob: float,
    decimal_odds: float,
    kelly_frac: float = 0.25,
    max_stake_pct: float = 0.05,
    min_stake: float = 1.0,
) -> float:
    """Compute stake using fractional Kelly, capped by max_stake_pct and floored by min_stake.

    Returns 0.0 if the calculated stake is below min_stake (no bet).
    """
    frac = fractional_kelly(true_prob, decimal_odds, kelly_frac)
    stake = frac * bankroll
    stake = min(stake, bankroll * max_stake_pct)
    if stake < min_stake:
        return 0.0
    return round(stake, 2)
