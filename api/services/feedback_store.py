"""Append-only JSONL storage for human feedback on generated reports.

Deliberately NOT going through job_store (in-memory, lost on restart) as the
persistence layer — feedback needs to survive process restarts to be usable
as v2 fine-tune training data later, so it's appended straight to disk, same
convention as dataset_generation/training_data.jsonl.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from api.config import settings

_lock = threading.Lock()


def append_feedback(record: dict, path: Path | None = None) -> None:
    """Append one JSON line to the feedback file, thread-safe.

    `path` is only meant to be overridden in tests (e.g. pytest's tmp_path) —
    production code should rely on the default (settings.archx_feedback_path).
    """
    target = path or settings.archx_feedback_path
    with _lock:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
