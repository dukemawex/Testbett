import pytest
from src.models.true_probability import implied_probability, devig, compute_edge


def test_implied_probability_even_odds():
    assert implied_probability(2.0) == 0.5


def test_implied_probability_various():
    assert abs(implied_probability(4.0) - 0.25) < 1e-9
    assert abs(implied_probability(1.25) - 0.8) < 1e-9


def test_implied_probability_non_positive_raises():
    with pytest.raises(ValueError):
        implied_probability(0.0)
    with pytest.raises(ValueError):
        implied_probability(-1.5)


def test_devig_sums_to_one():
    fair = devig(2.10, 3.40, 3.60)
    assert abs(sum(fair) - 1.0) < 1e-9


def test_devig_equal_odds():
    # All three outcomes at 3.0 → each probability = 1/3
    fair = devig(3.0, 3.0, 3.0)
    for p in fair:
        assert abs(p - 1 / 3) < 1e-9


def test_compute_edge_positive():
    # true_prob=0.55, odds=2.0 → implied=0.5 → edge=0.05
    assert abs(compute_edge(0.55, 2.0) - 0.05) < 1e-9


def test_compute_edge_negative():
    # true_prob=0.40, odds=2.0 → implied=0.5 → edge=-0.10
    assert abs(compute_edge(0.40, 2.0) - (-0.10)) < 1e-9


def test_compute_edge_zero():
    # true_prob=0.50, odds=2.0 → edge=0
    assert abs(compute_edge(0.50, 2.0)) < 1e-9
