#!/usr/bin/env python3
"""
demo.py
-------
Pipeline de démonstration complet pour Architect-Insight.

Usage (mode développeur, sans modèle fine-tuné) :
    python demo.py --repo /chemin/vers/un/repo --mock

Usage (avec modèle fine-tuné) :
    python demo.py --repo /chemin/vers/un/repo --model ./architect-insight-merged
"""

from __future__ import annotations

import argparse
import json

from api.services.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de démonstration Architect-Insight")
    parser.add_argument("--repo", required=True, help="Chemin vers le repository à analyser")
    parser.add_argument("--model", help="Chemin vers le modèle fine-tuné (optionnel)")
    parser.add_argument("--mock", action="store_true", help="Utilise un mock au lieu d'appeler un modèle")
    parser.add_argument("--language", default="fr", choices=["fr", "en"], help="Langue du rapport")
    parser.add_argument("--output", default="final_report.json", help="Fichier de sortie JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("Architect-Insight - Pipeline de démonstration")
    print("=" * 60)

    def on_progress(label: str, step: int) -> None:
        print(f"\n[{step}/5] {label}...")

    final_report = run_pipeline(
        args.repo,
        language=args.language,
        mock=args.mock,
        model_path=args.model,
        on_progress=on_progress,
    )

    summary = {
        "architecture": final_report["metrics"].get("architecture_pattern", "Inconnu"),
        "recommendation_type": final_report["recommendation"].get("recommendation", "Aucune"),
        "migration_cost_euro": final_report["cost_analysis"]["migration_cost"],
        "monthly_savings_euro": final_report["cost_analysis"]["monthly_savings"],
        "roi_months": final_report["cost_analysis"]["payback_months"],
        "risk": final_report["recommendation"].get("risk_assessment", "Non évalué"),
    }
    final_report["version"] = "1.0"
    final_report["summary"] = summary

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\nRapport sauvegardé dans {args.output}")
    print("=" * 60)
    print("Pipeline terminé avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    main()
