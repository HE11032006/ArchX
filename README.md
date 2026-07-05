# Architect-Insight — Outils de collecte (partie "sans IA")

Ce module correspond au bloc **OUTILS RÉELS** de l'architecture "Un Cerveau, Des
Outils" : il calcule des métriques **factuelles et reproductibles** sur un dépôt
Python, sans jamais faire appel à un LLM. C'est ce JSON qui sera injecté dans le
prompt du modèle Gemma fine-tuné — le modèle interprète et recommande, il
n'invente jamais de chiffres.

## Utilisation

```bash
python -m architect_insight.collector /chemin/vers/le/repo -o rapport.json
```

## Ce qui est calculé (et comment)

| Champ | Méthode | Fiabilité |
|---|---|---|
| `architecture_pattern` | Heuristique sur la structure de dossiers (manage.py, domain/, models/…) | Indicative — donne le pattern le plus probable + les preuves trouvées |
| `coupling_score` | Moyenne du nombre d'imports par fichier, normalisée /10 | Objective mais simple (ne capte pas le couplage sémantique) |
| `cohesion_score` | Proportion de classes "saines" (hors God Class) | Proxy heuristique — une vraie mesure LCOM nécessiterait une analyse des accès aux attributs |
| `avg_cyclomatic_complexity` | Algorithme de McCabe via `ast`, réimplémenté sans dépendance | Standard, identique à ce que calcule radon |
| `anti_patterns` | Seuils explicites (God Class, Long Method, Long Parameter List, High Coupling) | Objective — chaque seuil est documenté dans `patterns.py` |
| `test_coverage_estimate` | Ratio fonctions de test / fonctions de code | **Estimation grossière**, pas une vraie couverture de lignes (voir docstring) |
| `git_hotspots` | `git log --name-only` sur 12 mois + détection de commits "fix/bug/hotfix" | Factuel, basé sur l'historique réel |

## Pourquoi cette approche plutôt que de fine-tuner un modèle pour "prédire" ces chiffres

Un LLM fine-tuné pour générer directement des scores comme "couplage 7.2/10"
sans les calculer produit des chiffres qui *ressemblent* à des mesures mais
n'en sont pas — un jury technique posera la question "comment as-tu validé
ça ?" et il n'y aura pas de réponse solide. Ici, chaque chiffre est
recalculable et vérifiable indépendamment du modèle.

## Limites connues (à mentionner honnêtement dans la démo)

- `test_coverage_estimate` est un proxy, pas une couverture réelle — pour ça il
  faudrait exécuter `coverage run` sur la suite de tests du projet analysé.
- `cohesion_score` est une heuristique simple, pas une mesure LCOM complète.
- `architecture_pattern` peut se tromper sur des structures atypiques —
  c'est pour ça que le champ inclut `architecture_confidence` et
  `architecture_evidence`, pour que le modèle (et l'utilisateur) sachent
  combien s'y fier.
- Seul Python est géré pour l'instant (AST natif). Étendre à JS/TS
  nécessiterait un parseur externe (ex. `esprima`/`tree-sitter`).

## Prochaine étape

Le JSON produit ici devient le champ `"metrics"` du format d'entraînement
défini précédemment (voir `training_data.json`) : le modèle Gemma fine-tuné
reçoit ces vrais chiffres + la description du projet, et ne génère que
`analysis`, `recommendation`, `phases`, `risk_assessment`. Les valeurs
chiffrées comme `estimated_cost` et `roi_after_months` devraient elles aussi
être calculées par une fonction dédiée (heures de migration × taux horaire +
delta de coût cloud), pas générées par le modèle.
