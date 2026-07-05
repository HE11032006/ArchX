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
import sys
from pathlib import Path

# Import des modules du projet
from architect_insight.collector import collect
from training.format_for_training import build_user_message, SYSTEM_PROMPT
from architect_insight.metrics.cost_calculator import compute_full_report, cost_report_to_dict


def build_prompt_from_metrics(metrics: dict, language: str = "fr") -> str:
    """
    Construit le prompt utilisateur à partir des métriques réelles.
    Utilise EXACTEMENT la même fonction que l'entraînement.
    """
    # Reformater les métriques dans le format attendu par build_user_message
    input_data = {
        "sector": f"{metrics.get('architecture_pattern', 'Projet inconnu')}",
        "repo_path": metrics.get("repo_path", ""),
        "team_size": 8,  # valeur par défaut (le collecteur n'a pas cette info)
        "metrics": {
            "coupling_score": metrics.get("coupling_score", 0.0),
            "cohesion_score": metrics.get("cohesion_score", 0.0),
            "avg_cyclomatic_complexity": metrics.get("avg_cyclomatic_complexity", 0.0),
            "test_coverage_estimate": metrics.get("test_coverage_estimate", 0.0),
            "top_hotspot_bugfix_ratio": metrics.get("top_hotspot_bugfix_ratio", 0.0),
            "num_hotspots": metrics.get("num_hotspots", 0),
        },
        "anti_patterns": metrics.get("anti_patterns", []),
    }
    
    return build_user_message(language, input_data)


def call_model(prompt: str, model_path: str | None, mock: bool = False) -> dict:
    """Appelle le modèle (fine-tuné ou mock)."""
    if mock:
        # Mock : simule une réponse du modèle pour la démo
        return {
            "project_description": "Projet Django avec une dette technique modérée",
            "analysis": "L'équipe est mixte (60% juniors). La codebase Django a 4 ans, 120k lignes.",
            "recommendation": "refactoring",
            "phases": [
                {"phase": 1, "action": "Réduire la dette technique", "duration_days": 10},
                {"phase": 2, "action": "Améliorer les tests", "duration_days": 15},
            ],
            "risk_assessment": "Modéré",
        }
    
    if model_path:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Chargement du modèle depuis {model_path}...")
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            
            # Construire la conversation complète
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT["fr"]},
                {"role": "user", "content": prompt},
            ]
            formatted = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            inputs = tokenizer(formatted, return_tensors="pt").to("cuda")
            outputs = model.generate(
                **inputs,
                max_new_tokens=1000,
                temperature=0.3,
                do_sample=True,
            )
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            # Extraire le JSON de la réponse
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print("Aucun JSON trouvé dans la réponse, utilisation du mock.")
                return call_model(prompt, None, mock=True)
                
        except Exception as e:
            print(f"Erreur lors de l'appel du modèle: {e}")
            print("Utilisation du mock.")
            return call_model(prompt, None, mock=True)
    
    # Fallback : mock
    return call_model(prompt, None, mock=True)


def main():
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

    # Étape 1 : Collecte des métriques
    print("\n📊 Étape 1 : Collecte des métriques réelles...")
    metrics = collect(args.repo)
    print(f"   ✅ Analyse terminée : {metrics['files_analyzed']} fichiers analysés")
    print(f"   Architecture : {metrics['architecture_pattern']}")
    print(f"   Couplage : {metrics['coupling_score']}/10")
    print(f"   Complexité moyenne : {metrics['avg_cyclomatic_complexity']}")

    # Étape 2 : Construction du prompt
    print("\n🔄 Étape 2 : Construction du prompt pour le modèle...")
    prompt = build_prompt_from_metrics(metrics, args.language)
    print(f"   ✅ Prompt construit ({len(prompt)} caractères)")

    # Étape 3 : Appel du modèle (ou mock)
    print("\n🤖 Étape 3 : Génération de la recommandation...")
    recommendation = call_model(prompt, args.model, args.mock)
    print("   ✅ Recommandation générée")

    # Étape 4 : Calcul des coûts
    print("\n💰 Étape 4 : Calcul des coûts et ROI...")
    
    # Extraire la stack actuelle
    current_stack = metrics.get("architecture_pattern", "Django").split("(")[0].strip()
    
    # Déterminer la stack cible si migration recommandée
    target_stack = None
    if recommendation.get("recommendation") == "migration":
        # Essayer d'extraire la stack cible de l'analyse
        analysis = recommendation.get("analysis", "")
        if "Go" in analysis or "Rust" in analysis or "FastAPI" in analysis:
            target_stack = "Go"  # valeur par défaut
        else:
            target_stack = "FastAPI"
    
    # Extraire la durée et la taille d'équipe
    duration_days = 0
    team_size = 4
    if "phases" in recommendation:
        for phase in recommendation.get("phases", []):
            duration_days += phase.get("duration_days", 0)
    if "team_size_recommended" in recommendation:
        team_size = recommendation["team_size_recommended"]
    
    # Calculer le rapport
    report = compute_full_report(
        current_stack=current_stack,
        target_stack=target_stack,
        duration_days=duration_days,
        team_size=team_size,
        current_cloud_cost=None,  # estimation automatique
        scale="medium",
        hourly_rate=80.0,
    )
    cost_data = cost_report_to_dict(report)
    print(f"   ✅ Coût de migration : {cost_data['migration_cost']:,.0f} €")
    print(f"   Économies mensuelles : {cost_data['monthly_savings']:,.0f} €")
    print(f"   ROI : {cost_data['roi_months']:.1f} mois")

    # Étape 5 : Rapport final
    print("\n📋 Étape 5 : Génération du rapport final...")
    final_report = {
        "version": "1.0",
        "date": "2026-07-06",
        "repo": args.repo,
        "metrics": metrics,
        "recommendation": recommendation,
        "cost_analysis": cost_data,
        "summary": {
            "architecture": metrics.get("architecture_pattern", "Inconnu"),
            "recommendation_type": recommendation.get("recommendation", "Aucune"),
            "migration_cost_euro": cost_data["migration_cost"],
            "monthly_savings_euro": cost_data["monthly_savings"],
            "roi_months": cost_data["roi_months"],
            "risk": recommendation.get("risk_assessment", "Non évalué"),
        }
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Rapport sauvegardé dans {args.output}")

    print("\n" + "=" * 60)
    print("🎉 Pipeline terminé avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    main()