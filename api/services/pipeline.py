"""Analysis pipeline extracted from demo.py for reuse by CLI and API."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from datetime import date
from typing import Any

from architect_insight.collector import collect
from architect_insight.metrics.cost_calculator import compute_full_report, cost_report_to_dict
from training.format_for_training import SYSTEM_PROMPT, build_user_message

from api.services.health import compute_health_band

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, int], None]

STEP_LABELS = {
    1: "Collecting metrics",
    2: "Building prompt",
    3: "Generating recommendation",
    4: "Computing costs",
    5: "Finalizing report",
}


def _detected_language(metrics: dict) -> str | None:
    """Real signal only: manifest-detected languages (architect_insight.metrics.dependencies).

    Deliberately does NOT guess a framework — nothing in the collector output
    names one reliably, and asserting a wrong guess is worse than omitting it
    (see the fine-tuned model's hallucination fix in training/format_for_training.py).
    """
    detected = metrics.get("dependencies", {}).get("languages", {})
    return ", ".join(sorted(detected)) if detected else None


def _detected_database(metrics: dict) -> str | None:
    database = metrics.get("database", {})
    if not database.get("has_database"):
        return None
    detected = database.get("detected_databases", [])
    return ", ".join(detected) if detected and detected != ["Non détecté"] else None


def build_prompt_from_metrics(metrics: dict, language: str = "fr") -> str:
    input_data = {
        "sector": f"{metrics.get('architecture_pattern', 'Projet inconnu')}",
        "repo_path": metrics.get("repo_path", ""),
        "team_size": 8,
        "metrics": {
            "coupling_score": metrics.get("coupling_score", 0.0),
            "cohesion_score": metrics.get("cohesion_score", 0.0),
            "avg_cyclomatic_complexity": metrics.get("avg_cyclomatic_complexity", 0.0),
            "test_coverage_estimate": metrics.get("test_coverage_estimate", 0.0),
            "top_hotspot_bugfix_ratio": metrics.get("top_hotspot_bugfix_ratio", 0.0),
            "num_hotspots": metrics.get("num_hotspots", 0),
        },
        "anti_patterns": metrics.get("anti_patterns", []),
        "language": _detected_language(metrics),
        "database_name": _detected_database(metrics),
    }
    return build_user_message(language, input_data)


def call_model(prompt: str, model_path: str | None, mock: bool = False, language: str = "fr") -> dict:
    if mock:
        return {
            "project_description": "Projet avec une dette technique modérée identifiée par l'analyse.",
            "analysis": (
                "Les métriques collectées indiquent des axes d'amélioration sur la structure "
                "et la couverture de tests."
            ),
            "recommendation": "refactoring",
            "phases": [
                {"phase": 1, "action": "Réduire la dette technique", "duration_days": 10},
                {"phase": 2, "action": "Améliorer les tests", "duration_days": 15},
            ],
            "risk_assessment": "Modéré",
            "inference_mode": "mock",
        }

    if model_path:
        try:
            import torch
            from transformers import AutoModelForMultimodalLM, AutoProcessor

            # Gemma 4 12B Unified is multimodal — AutoModelForMultimodalLM + AutoProcessor
            # is the officially documented loading path (not AutoModelForCausalLM),
            # same as training/finetune_lora_amd.ipynb. Keeping this in sync with the
            # notebook is critical: a prior mismatch here (Gemma 2 prod vs. a locally
            # duplicated Gemma 3 training format) caused the model to learn a prompt
            # format it never saw again in production.
            processor = AutoProcessor.from_pretrained(model_path)
            model = AutoModelForMultimodalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )

            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT[language]}]},
                {"role": "user", "content": [{"type": "text", "text": prompt}]},
            ]
            inputs = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(model.device, dtype=torch.bfloat16)

            outputs = model.generate(
                **inputs,
                max_new_tokens=1000,
                temperature=0.3,
                do_sample=True,
            )
            response = processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group()) | {"inference_mode": "fine-tuned"}
        except Exception:
            logger.exception("Fine-tuned model inference failed, falling back to mock")

    return call_model(prompt, None, mock=True, language=language)


def _phase_duration_days(phase: dict) -> float:
    """Extract a duration estimate in days from a phase dict.

    The fine-tuned model emits `duration_days_range` (e.g. "15-20") rather than
    a single `duration_days` int — average the range as a point estimate.
    Falls back to `duration_days` if present, for older data/other formats.
    """
    if phase.get("duration_days") is not None:
        return phase["duration_days"] or 0

    duration_range = phase.get("duration_days_range")
    if not duration_range:
        return 0

    numbers = [int(n) for n in re.findall(r"\d+", str(duration_range))]
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def _normalize_metrics(metrics: dict) -> dict:
    """Normalize collector output for frontend consumption."""
    normalized = dict(metrics)

    anti_patterns = normalized.get("anti_patterns", [])
    normalized["anti_patterns"] = [
        p["type"] if isinstance(p, dict) else str(p)
        for p in anti_patterns
    ]

    return normalized


def run_pipeline(
    repo_path: str,
    *,
    language: str = "fr",
    mock: bool = False,
    model_path: str | None = None,
    team_size: int = 8,
    hourly_rate: float = 80.0,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    def progress(step: int) -> None:
        if on_progress:
            on_progress(STEP_LABELS[step], step)

    progress(1)
    raw_metrics = collect(repo_path)
    metrics = _normalize_metrics(raw_metrics)

    progress(2)
    prompt = build_prompt_from_metrics(raw_metrics, language)

    progress(3)
    recommendation = call_model(prompt, model_path, mock=mock, language=language)
    inference_mode = recommendation.pop("inference_mode", "mock")

    progress(4)
    current_stack = metrics.get("architecture_pattern", "Django").split("(")[0].strip()

    target_stack = None
    if recommendation.get("recommendation") == "migration":
        analysis = recommendation.get("analysis", "")
        if "Go" in analysis or "Rust" in analysis or "FastAPI" in analysis:
            target_stack = "Go"
        else:
            target_stack = "FastAPI"

    duration_days = 0
    effective_team_size = team_size
    for phase in recommendation.get("phases", []):
        duration_days += _phase_duration_days(phase)
    duration_days = round(duration_days)
    if "team_size_recommended" in recommendation:
        effective_team_size = recommendation["team_size_recommended"]

    cost_report = compute_full_report(
        current_stack=current_stack,
        target_stack=target_stack,
        duration_days=duration_days,
        team_size=effective_team_size,
        current_cloud_cost=None,
        scale="medium",
        hourly_rate=hourly_rate,
    )
    cost_data = cost_report_to_dict(cost_report)

    progress(5)
    health_band = compute_health_band(raw_metrics)

    return {
        "repo": repo_path,
        "date": date.today().isoformat(),
        "metrics": metrics,
        "recommendation": recommendation,
        "inference_mode": inference_mode,
        "cost_analysis": {
            "migration_cost": cost_data["migration_cost"],
            "current_cloud_cost": cost_data["current_cloud_cost"],
            "target_cloud_cost": cost_data["target_cloud_cost"],
            "monthly_savings": cost_data["monthly_savings"],
            "payback_months": cost_data.get("payback_months", cost_data.get("roi_months", 0)),
            "cost_confidence": "medium",
        },
        "health_band": health_band,
    }
