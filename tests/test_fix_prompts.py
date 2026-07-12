"""Regression tests for the deterministic, template-based fix-prompt generator.

Pure string formatting, no LLM call — locks in: correct template per real
anti-pattern type, "Fichier non analysable" (a parse-error marker, not a real
anti-pattern) never gets a prompt, the generic fallback fires only when there
are zero real findings AND some metrics signal exists, and the empty case
returns [] rather than crashing.
"""

from architect_insight.metrics.fix_prompts import generate_fix_prompts

_METRICS = {
    "coupling_score": 8.0,
    "cohesion_score": 2.0,
    "avg_cyclomatic_complexity": 12.0,
    "architecture_pattern": "Express",
    "complexity_hotspots": [
        {"file": "src/app.js", "max_complexity": 14},
        {"file": "src/utils.js", "max_complexity": 6},
    ],
}


def _finding(type_, location="src/foo.py:Foo (L10)", detail="some detail"):
    return {"type": type_, "location": location, "severity": "high", "detail": detail}


def test_god_class_template():
    prompts = generate_fix_prompts([_finding("God Class")])
    assert len(prompts) == 1
    assert prompts[0]["type"] == "God Class"
    assert "src/foo.py:Foo (L10)" in prompts[0]["prompt"]
    assert "some detail" in prompts[0]["prompt"]
    assert prompts[0]["fallback"] is False


def test_long_method_template():
    prompts = generate_fix_prompts([_finding("Long Method")])
    assert "Extract Method" in prompts[0]["prompt"]


def test_long_parameter_list_template():
    prompts = generate_fix_prompts([_finding("Long Parameter List")])
    assert "Parameter Object" in prompts[0]["prompt"]


def test_high_coupling_template():
    prompts = generate_fix_prompts([_finding("High Coupling (fichier)")])
    assert "coupling" in prompts[0]["prompt"].lower()


def test_parse_error_marker_never_gets_a_prompt():
    prompts = generate_fix_prompts([_finding("Fichier non analysable")])
    assert prompts == []


def test_caps_at_max_prompts():
    findings = [_finding("God Class", location=f"f{i}.py:C (L1)") for i in range(10)]
    prompts = generate_fix_prompts(findings, max_prompts=6)
    assert len(prompts) == 6


def test_fallback_when_no_real_findings_but_metrics_present():
    prompts = generate_fix_prompts([], metrics=_METRICS)
    assert len(prompts) == 1
    assert prompts[0]["fallback"] is True
    assert prompts[0]["location"] == "src/app.js"  # highest complexity hotspot
    assert "8.0" in prompts[0]["prompt"]


def test_no_findings_no_metrics_returns_empty():
    assert generate_fix_prompts([]) == []
    assert generate_fix_prompts([], metrics={}) == []


def test_no_findings_metrics_without_hotspots_returns_empty():
    assert generate_fix_prompts([], metrics={"coupling_score": 1.0}) == []
