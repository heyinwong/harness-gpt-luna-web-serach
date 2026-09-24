"""Conservative precision planning, never a power guarantee or a pass prediction."""
import math


def required_questions(variance, support_width, slack, alpha):
    if slack <= 0:
        return None
    logterm = math.log(4 / alpha)
    def radius(n):
        return math.sqrt(2 * variance * logterm / n) + 7 * support_width * logterm / (3 * (n - 1))
    lo, hi = 2, 2
    while radius(hi) > slack and hi < 10000000:
        hi *= 2
    if hi >= 10000000:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if radius(mid) <= slack:
            hi = mid
        else:
            lo = mid + 1
    return lo


def precision_plan(result):
    alpha = (1 - result["confidence_level"]) / result["simultaneous_coordinates"]
    plans = []
    for row in result["rows"]:
        if row["kind"] == "mean_difference":
            slack, width = row["margin"], 2 * row["cap"]
        elif row["kind"] == "total_variation":
            slack, width = 2 * row["margin"] / len(row["coordinate_intervals"]), 2
        else:
            slack = 1-row["margin"] if row["direction"] == "minimum" else row["margin"]
            width = 1
        plans.append({"scope": row["scope"], "metric": row["name"],
                      "optimistic_zero_variance_questions": required_questions(0, width, slack, alpha)})
    return {"notice": "Optimistic precision floor assuming zero difference and zero variance (perfect reliability for quality gates). Actual variance or a gap increases sample requirements; a gap outside tolerance requires a design change. Counts are independent questions per scope, not model repetitions. This is not a power calculation.",
            "requirements": plans,
            "largest_per_scope_floor": max(p["optimistic_zero_variance_questions"] or 0 for p in plans)}
