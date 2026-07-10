"""Compute project health band from collected metrics."""

from __future__ import annotations


def compute_health_band(metrics: dict) -> str:
    """
    Returns 'healthy', 'warning', or 'critical' based on objective thresholds.
    """
    coupling = metrics.get("coupling_score", 0.0)
    cohesion = metrics.get("cohesion_score", 0.0)
    coverage = metrics.get("test_coverage_estimate", 0.0)
    anti_patterns = metrics.get("anti_patterns", [])
    complexity = metrics.get("avg_cyclomatic_complexity", 0.0)

    high_severity = sum(
        1 for p in anti_patterns
        if isinstance(p, dict) and p.get("severity") == "high"
    )

    score = 0
    if coupling > 7:
        score += 2
    elif coupling > 4:
        score += 1

    if cohesion < 4:
        score += 2
    elif cohesion < 6:
        score += 1

    if coverage < 40:
        score += 2
    elif coverage < 60:
        score += 1

    if complexity > 8:
        score += 1

    if high_severity >= 3:
        score += 2
    elif high_severity >= 1:
        score += 1

    if score >= 4:
        return "critical"
    if score >= 2:
        return "warning"
    return "healthy"
