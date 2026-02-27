def brier_score(predicted_probs: list[float], outcomes: list[int]) -> float:
    """Brier score: mean((p - o)^2). Lower is better.

    Args:
        predicted_probs: Predicted probabilities in [0, 1].
        outcomes: Actual binary outcomes (0 or 1).

    Returns:
        Mean squared error between predictions and outcomes.
    """
    if len(predicted_probs) != len(outcomes):
        raise ValueError("predicted_probs and outcomes must have the same length")
    if not predicted_probs:
        return 0.0
    return sum((p - o) ** 2 for p, o in zip(predicted_probs, outcomes)) / len(predicted_probs)


def calibrate_probabilities(probs: list[float], outcomes: list[int]) -> float:
    """Return a simple scaling factor to calibrate probabilities.

    Uses the ratio of observed frequency to mean predicted probability as a
    multiplicative correction (isotonic regression placeholder).

    Args:
        probs: List of predicted probabilities.
        outcomes: Corresponding binary outcomes (0 or 1).

    Returns:
        Scaling factor (multiply predictions by this to improve calibration).
    """
    if not probs or not outcomes:
        return 1.0
    mean_pred = sum(probs) / len(probs)
    mean_obs = sum(outcomes) / len(outcomes)
    if mean_pred == 0:
        return 1.0
    return mean_obs / mean_pred
