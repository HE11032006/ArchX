"""Regression tests for the RLHF feedback persistence layer.

Locks in: append_feedback writes durable JSONL (survives process restart,
unlike job_store's in-memory Job dict) and accumulates rather than overwriting.
"""

import json

from api.services.feedback_store import append_feedback


def test_append_feedback_writes_one_json_line(tmp_path):
    path = tmp_path / "feedback" / "collected_feedback.jsonl"
    record = {"id": "abc", "rating": "up", "correction": None}

    append_feedback(record, path=path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


def test_append_feedback_accumulates_multiple_calls(tmp_path):
    path = tmp_path / "collected_feedback.jsonl"

    append_feedback({"id": "1", "rating": "up"}, path=path)
    append_feedback({"id": "2", "rating": "down"}, path=path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["id"] for line in lines] == ["1", "2"]


def test_append_feedback_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "feedback.jsonl"
    assert not path.parent.exists()

    append_feedback({"id": "1"}, path=path)

    assert path.exists()
