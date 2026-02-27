def bayesian_update_lambda(
    prior_lambda: float,
    observed_goals: list[float],
    alpha: float = 1.0,
) -> float:
    """Gamma-Poisson conjugate update for a Poisson rate parameter.

    Model
    -----
    Likelihood : X_i | λ ~ Poisson(λ)
    Prior      : λ ~ Gamma(α, β)  with β = α / prior_lambda so E[λ] = prior_lambda
    Posterior  : λ | X ~ Gamma(α + ΣX_i, β + n)
    Posterior mean = (α + ΣX_i) / (β + n)
                   = (α + ΣX_i) / (α / prior_lambda + n)

    Args:
        prior_lambda: Prior belief about scoring rate (prior mean).
        observed_goals: Goals scored in recent matches.
        alpha: Shape parameter for the Gamma prior (default 1.0).

    Returns:
        Updated lambda (posterior mean).
    """
    if not observed_goals:
        return prior_lambda

    beta = alpha / prior_lambda if prior_lambda > 0 else 1.0
    n = len(observed_goals)
    total_goals = sum(observed_goals)
    return (alpha + total_goals) / (beta + n)
