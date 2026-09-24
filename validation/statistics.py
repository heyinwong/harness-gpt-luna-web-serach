"""Bounded question-cluster confidence intervals; no model calls.

Empirical Bernstein: Maurer & Pontil (2009), Theorem 4. Applying the
one-sided theorem to X and -X gives the two-sided bound used here.
Bonferroni allocates alpha across all registered coordinates and strata.
"""
import math
import statistics


def mean(values):
    return sum(values) / len(values)


def bounded_interval(values, lower, upper, alpha):
    """Finite-sample CI under independent identically distributed question clusters.

    Repeated model runs must be averaged within question before this function.
    Empty or one-question samples return the entire support, never certainty.
    """
    if not lower < upper or not 0 < alpha < 1:
        raise ValueError("Invalid support or alpha")
    if any(not math.isfinite(x) or x < lower - 1e-9 or x > upper + 1e-9 for x in values):
        raise ValueError("Observation outside declared metric support")
    if not values:
        return {"estimate": None, "low": lower, "high": upper, "n_questions": 0}
    center = mean(values)
    if len(values) < 2:
        return {"estimate": center, "low": lower, "high": upper, "n_questions": len(values)}
    n = len(values)
    logterm = math.log(4 / alpha)
    radius = math.sqrt(2 * statistics.variance(values) * logterm / n) + 7 * (upper - lower) * logterm / (3 * (n - 1))
    return {"estimate": center, "low": max(lower, center - radius), "high": min(upper, center + radius), "n_questions": n}


def equivalence(interval, margin):
    if interval["estimate"] is None:
        return "inconclusive"
    if interval["low"] >= -margin and interval["high"] <= margin:
        return "equivalent"
    if interval["low"] > margin or interval["high"] < -margin:
        return "different"
    return "inconclusive"


def total_variation_interval(coordinate_intervals):
    """Propagate simultaneous bin-difference CIs to TV distance in [0,1]."""
    lower = sum(0 if x["low"] <= 0 <= x["high"] else min(abs(x["low"]), abs(x["high"]))
                for x in coordinate_intervals) / 2
    upper = sum(max(abs(x["low"]), abs(x["high"])) for x in coordinate_intervals) / 2
    point = sum(abs(x["estimate"]) for x in coordinate_intervals) / 2
    return {"estimate": min(1, point), "low": min(1, lower), "high": min(1, upper)}


def distribution_verdict(interval, margin):
    if interval["high"] <= margin:
        return "equivalent"
    if interval["low"] > margin:
        return "different"
    return "inconclusive"
