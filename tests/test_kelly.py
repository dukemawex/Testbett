import pytest
from src.execution.kelly import kelly_fraction, fractional_kelly, compute_stake


def test_kelly_positive_edge():
    # true_prob=0.55, odds=2.0 → b=1, f=(1*0.55 - 0.45)/1 = 0.10
    f = kelly_fraction(0.55, 2.0)
    assert abs(f - 0.10) < 1e-9


def test_kelly_negative_edge_returns_zero():
    # true_prob=0.40, odds=2.0 → f=(0.40-0.60)/1 = -0.20 → clamped to 0
    assert kelly_fraction(0.40, 2.0) == 0.0


def test_kelly_breakeven_returns_zero():
    # true_prob=0.50, odds=2.0 → f=0 exactly
    assert kelly_fraction(0.50, 2.0) == 0.0


def test_kelly_odds_le_one_returns_zero():
    assert kelly_fraction(0.9, 1.0) == 0.0


def test_fractional_kelly_applies_multiplier():
    full = kelly_fraction(0.55, 2.0)
    frac = fractional_kelly(0.55, 2.0, fraction=0.25)
    assert abs(frac - 0.25 * full) < 1e-9


def test_compute_stake_basic():
    stake = compute_stake(
        bankroll=1000.0,
        true_prob=0.55,
        decimal_odds=2.0,
        kelly_frac=0.25,
        max_stake_pct=0.05,
        min_stake=1.0,
    )
    # fractional Kelly = 0.25 * 0.10 = 0.025 → 25.0; capped at 5% of 1000 = 50
    assert stake == 25.0


def test_compute_stake_capped_by_max_pct():
    # Use a very high true_prob to force stake above max_stake_pct
    stake = compute_stake(
        bankroll=1000.0,
        true_prob=0.99,
        decimal_odds=1.5,
        kelly_frac=1.0,
        max_stake_pct=0.05,
        min_stake=1.0,
    )
    assert stake <= 50.0  # 5% of 1000


def test_compute_stake_below_min_returns_zero():
    # Tiny bankroll → stake below min_stake
    stake = compute_stake(
        bankroll=10.0,
        true_prob=0.51,
        decimal_odds=2.0,
        kelly_frac=0.25,
        max_stake_pct=0.05,
        min_stake=5.0,
    )
    assert stake == 0.0
