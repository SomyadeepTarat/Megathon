"""Checks consume teammates' outputs; they do not duplicate their engines."""
import math


def close(actual, expected, label, tolerance=.02):
    if actual is None or not math.isfinite(actual) or not math.isclose(actual, expected, abs_tol=tolerance, rel_tol=1e-6):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def check_energy(result, factors=None):
    baseline, after, savings = (result[k] for k in ["baseline", "after", "savings"])
    for fuel in ["electricity_kwh", "gas_kwh"]:
        for state in [baseline, after]:
            if state[fuel] is None or not math.isfinite(state[fuel]) or state[fuel] < 0:
                raise AssertionError(f"Invalid {fuel}; missing values must not become zero")
        close(savings[fuel], baseline[fuel] - after[fuel], fuel)
    net = savings["electricity_kwh"] + savings["gas_kwh"]
    close(savings["net_kwh"], net, "net savings")
    total = sum(baseline.values()) if set(baseline) == {"electricity_kwh", "gas_kwh"} else baseline["electricity_kwh"] + baseline["gas_kwh"]
    if total == 0:
        if savings["percentage"] is not None:
            raise AssertionError("Zero baseline requires unavailable percentage")
    else:
        close(savings["percentage"], 100 * net / total, "percentage")
    if factors is not None:
        expected = savings["electricity_kwh"] * factors["electricity"] + savings["gas_kwh"] * factors["gas"]
        close(result["carbon"]["reduction_kg_co2e"], expected, "carbon")


def check_score(result):
    components = result["components"]
    expected = sorted([.25, .20, .15, .15, .10, .10, .05])
    if len(components) != 7 or sorted(c["weight"] for c in components) != expected:
        raise AssertionError("Score requires seven PRD weights")
    for component in components:
        if not 0 <= component["subscore"] <= 100:
            raise AssertionError("Subscore outside [0,100]")
        close(component["contribution"], component["subscore"] * component["weight"], "contribution")
    close(result["score"], round(sum(c["contribution"] for c in components)), "rounded score", 0)
    score = result["score"]
    category = "Highly efficient" if score >= 80 else "Good" if score >= 65 else "Moderate" if score >= 50 else "Poor" if score >= 30 else "Very poor"
    if result["classification"] != category:
        raise AssertionError("Classification must use rounded final score")


def check_monotonicity(calculate, ordered_states):
    """Call a teammate's adapter on states ordered from worse to better."""
    scores = [calculate(state)["score"] for state in ordered_states]
    if any(a > b for a, b in zip(scores, scores[1:])):
        raise AssertionError(f"Improvement decreased score: {scores}")
    if scores != [calculate(state)["score"] for state in ordered_states]:
        raise AssertionError("Score is not reproducible")
