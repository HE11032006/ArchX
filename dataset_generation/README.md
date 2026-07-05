# Architect-Insight — Génération du dataset de fine-tuning

## Fichiers

| Fichier | Rôle |
|---|---|
| `scenario_axes.py` | Définit les axes de variation et échantillonne des scénarios uniques, avec 3 bandes de santé (healthy/moderate/critical) réparties 30/40/30 pour forcer la diversité des conclusions |
| `teacher_prompts.py` | Construit les prompts bilingues (FR/EN) envoyés au modèle enseignant, avec les garde-fous écrits en dur (pas de $/€/ROI inventés, recommandation justifiée par les métriques) |
| `generate_dataset.py` | Orchestrateur : appelle le teacher, valide chaque réponse, écrit le JSONL final + un fichier séparé pour les cas à relire |
| `test_validation.py` | Tests de la logique de validation avec des réponses simulées (aucun appel réseau) |

## Pourquoi la bande "healthy" existe

Sans elle, un dataset généré naïvement pousse le teacher model à toujours recommander une migration (c'est plus "intéressant" à écrire). Le modèle fine-tuné hériterait de ce biais et deviendrait un partisan systématique du rewrite — l'inverse d'un architecte senior. 30% des scénarios ont des métriques objectivement saines, et le system prompt interdit explicitement de recommander une migration dans ce cas sans justification.

## Utilisation

```bash
# 1. Vérifier que tout fonctionne sans consommer d'appels API
python -m dataset_generation.test_validation
python -m dataset_generation.generate_dataset --n 20 --dry-run

# 2. Génération réelle (nécessite ANTHROPIC_API_KEY et `pip install anthropic`)
export ANTHROPIC_API_KEY=sk-...
python -m dataset_generation.generate_dataset --n 400 --languages fr en --out training_data.jsonl
```

Avec `--n 400` et les 2 langues, tu obtiens jusqu'à 800 exemples bruts. Un tri automatique sépare :
- `training_data.jsonl` — exemples valides, prêts pour le fine-tuning
- `to_review.jsonl` — exemples rejetés (JSON invalide, garde-fou déclenché) ou juste flagués pour relecture manuelle (incohérence métriques/recommandation détectée par heuristique)

**Relis `to_review.jsonl` avant de lancer le fine-tuning** — c'est rapide (quelques dizaines d'exemples au pire) et c'est ce qui évite d'entraîner sur du bruit.

## Bug corrigé pendant les tests (pour référence)

La première version de la détection "healthy + recommande une migration" se déclenchait à tort sur "**ne pas** migrer" (le mot "migrer" matchait quand même). Corrigé via `_recommends_migration()` qui vérifie d'abord les tournures de négation. Les 6 tests dans `test_validation.py` couvrent ce cas — à ne pas supprimer si tu modifies la regex plus tard.

## Ce qu'il reste à construire

1. **`cost_calculator.py`** — la fonction qui calcule `estimated_cost` et `roi_after_months` à partir de `phases` (heures × taux horaire) + du delta de coût cloud entre stack actuelle et cible. Volontairement séparée du LLM (voir toute la discussion précédente sur l'anti-pattern des chiffres inventés).
2. **Le script LoRA corrigé** (bf16 sans bitsandbytes, `SFTTrainer` + chat template Gemma natif) — déjà cadré dans notre échange précédent, pas encore écrit en fichier.
3. Brancher `collector.py` (les vraies métriques d'un repo) en entrée du modèle fine-tuné final, à la place des scénarios synthétiques — c'est le pipeline de démo.
