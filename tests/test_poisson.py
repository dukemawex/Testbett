import math
import pytest
from src.models.poisson import poisson_pmf, score_matrix, compute_probabilities


def test_poisson_pmf_known_value():
    # P(X=0 | λ=1.5) = e^{-1.5} ≈ 0.2231
    assert abs(poisson_pmf(0, 1.5) - math.exp(-1.5)) < 1e-9


def test_poisson_pmf_k1():
    # P(X=1 | λ=1.5) = 1.5 * e^{-1.5}
    expected = 1.5 * math.exp(-1.5)
    assert abs(poisson_pmf(1, 1.5) - expected) < 1e-9


def test_poisson_pmf_lambda_zero_k0():
    assert poisson_pmf(0, 0) == 1.0


def test_poisson_pmf_lambda_zero_k1():
    assert poisson_pmf(1, 0) == 0.0


def test_score_matrix_sums_to_one():
    matrix = score_matrix(1.5, 1.2)
    total = sum(cell for row in matrix for cell in row)
    assert abs(total - 1.0) < 1e-6


def test_compute_probabilities_sum_to_one():
    result = compute_probabilities(1.5, 1.2)
    total = result.home_win_prob + result.draw_prob + result.away_win_prob
    assert abs(total - 1.0) < 1e-4


def test_compute_probabilities_over_under_complement():
    result = compute_probabilities(1.5, 1.2)
    # over + under should sum to 1.0 (all scorelines are covered)
    assert abs(result.over_prob + result.under_prob - 1.0) < 1e-4


def test_compute_probabilities_lambda_zero():
    # With λ=0 for both teams, only 0-0 is possible → draw probability ≈ 1
    result = compute_probabilities(0.0, 0.0)
    assert abs(result.draw_prob - 1.0) < 1e-6
    assert abs(result.home_win_prob) < 1e-9
    assert abs(result.away_win_prob) < 1e-9


def test_compute_probabilities_high_home_lambda():
    # Strong home team should have high home win probability
    result = compute_probabilities(4.0, 0.5)
    assert result.home_win_prob > result.away_win_prob
