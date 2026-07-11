"""Regression tests for the language/database stack-fields fix.

Root cause: dataset_generation/teacher_prompts.py told the Teacher model to
narrate the project's stack in project_description, but
dataset_generation/generate_dataset.py never saved that stack info into the
student's `input` — so the fine-tuned model learned to always invent a stack
(confirmed via a manual test: it invented ".NET/ASP.NET Core with SQL Server").
These tests lock in the fix: only genuinely-derivable fields (language,
database) flow from collector.py into the prompt, and format_for_training.py
only renders a stack line when they're actually present.
"""

from api.services.pipeline import _detected_database, _detected_language
from training.format_for_training import build_user_message


def test_detected_language_from_manifest_dependencies():
    metrics = {"dependencies": {"languages": {"Python": {}, "JavaScript": {}}}}
    assert _detected_language(metrics) == "JavaScript, Python"


def test_detected_language_absent_when_no_manifests_found():
    assert _detected_language({"dependencies": {"languages": {}}}) is None
    assert _detected_language({}) is None


def test_detected_database_present():
    metrics = {"database": {"has_database": True, "detected_databases": ["PostgreSQL"]}}
    assert _detected_database(metrics) == "PostgreSQL"


def test_detected_database_absent_when_not_found():
    assert _detected_database({"database": {"has_database": False}}) is None
    assert _detected_database({"database": {"has_database": True, "detected_databases": ["Non détecté"]}}) is None
    assert _detected_database({}) is None


def test_build_user_message_renders_stack_line_when_present():
    prompt = build_user_message("fr", {"sector": "e-commerce", "language": "Python", "database_name": "PostgreSQL"})
    assert "Stack connue : Python, PostgreSQL" in prompt


def test_build_user_message_omits_stack_line_when_absent():
    prompt = build_user_message("fr", {"sector": "e-commerce"})
    assert "Stack connue" not in prompt
