"""
test_validation.py
--------------------
Vérifie que validate_output() attrape bien ce qu'elle est censée attraper,
avec des réponses de teacher model SIMULÉES (aucun appel réseau).
"""
from .scenario_axes import Scenario
from .generate_dataset import validate_output

def make_scenario(health_band: str, stack_known: bool = True) -> Scenario:
    return Scenario(
        scenario_id="scn_test", sector="e-commerce", team_size=10, pct_junior=50,
        pct_senior=50, codebase_age_years=3.0, language="Python", framework="Django",
        database="PostgreSQL", dominant_constraint="coût cloud", health_band=health_band,
        metrics={"coupling_score": 2.0}, anti_patterns=[], stack_known=stack_known,
    )

CASES = []

# 1. Réponse propre, bande "critical", recommande bien une action -> doit passer sans flag
CASES.append((
    "OK - critical avec action",
    make_scenario("critical"),
    '{"project_description": "...", "analysis": "Couplage élevé.", '
    '"recommendation": "Migrer progressivement le module de paiement vers un service dédié.", '
    '"phases": [{"phase": 1, "action": "Isoler le module paiement", "duration_days_range": "10-15 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=False),
))

# 2. Réponse avec un montant en euros malgré la consigne -> doit être rejetée (garde-fou)
CASES.append((
    "REJET - montant € halluciné",
    make_scenario("critical"),
    '{"project_description": "...", "analysis": "...", '
    '"recommendation": "Migrer vers Go, coût estimé 45000€.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "10-15 jours"}], '
    '"risk_assessment": "..."}',
    dict(ok=False),
))

# 3. Champ manquant ("risk_assessment" absent) -> doit être rejetée
CASES.append((
    "REJET - champ manquant",
    make_scenario("moderate"),
    '{"project_description": "...", "analysis": "...", '
    '"recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}]}',
    dict(ok=False),
))

# 4. Bande "healthy" mais le teacher recommande quand même une migration -> flag pour relecture
CASES.append((
    "FLAG - healthy mais recommande une migration",
    make_scenario("healthy"),
    '{"project_description": "...", "analysis": "Tout va bien mais...", '
    '"recommendation": "Migrer vers Go pour anticiper.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Faible"}',
    dict(ok=True, needs_review=True),
))

# 5. Bande "healthy", pas de migration recommandée -> cas idéal, pas de flag
CASES.append((
    "OK - healthy, pas de migration",
    make_scenario("healthy"),
    '{"project_description": "...", "analysis": "Le projet est sain.", '
    '"recommendation": "Ne pas migrer, continuer les bonnes pratiques actuelles et renforcer les tests.", '
    '"phases": [], "risk_assessment": "Faible"}',
    dict(ok=True, needs_review=False),
))

# 6. Réponse entourée de balises markdown ```json ... ``` -> doit quand même être parsée
CASES.append((
    "OK - JSON entouré de ```json",
    make_scenario("moderate"),
    '```json\n{"project_description": "...", "analysis": "...", '
    '"recommendation": "Refactoring ciblé du module legacy.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}\n```',
    dict(ok=True, needs_review=False),
))

# 7. project_description mentionne une stack différente de celle du scénario (Python/Django/
#    PostgreSQL) -> flag pour relecture (root cause du bug de hallucination de stack)
CASES.append((
    "FLAG - project_description mentionne une stack étrangère au scénario",
    make_scenario("moderate"),
    '{"project_description": "Plateforme mature construite en .NET/ASP.NET Core avec SQL Server.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=True),
))

# 8. project_description ne mentionne QUE la vraie stack du scénario -> pas de flag
CASES.append((
    "OK - project_description mentionne la vraie stack (Python/Django/PostgreSQL)",
    make_scenario("moderate"),
    '{"project_description": "Plateforme e-commerce en Python/Django avec PostgreSQL.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=False),
))

# 9. stack_known=False mais le teacher mentionne quand même la stack (même la "vraie")
#    -> flag, car cette info n'est par construction pas censée être connue
CASES.append((
    "FLAG - stack_known=False mais stack mentionnée quand même",
    make_scenario("moderate", stack_known=False),
    '{"project_description": "Plateforme e-commerce construite en Python/Django.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=True),
))

# 10. stack_known=False et le teacher reste bien générique -> pas de flag
CASES.append((
    "OK - stack_known=False, description générique sans techno",
    make_scenario("moderate", stack_known=False),
    '{"project_description": "Plateforme e-commerce avec une dette technique modérée.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=False),
))

# 11. project_description narre l'âge du projet (donné au teacher en contexte interne
#     uniquement) -> flag (root cause du 2e bug de hallucination, jamais corrigé avant)
CASES.append((
    "FLAG - âge du projet narré dans project_description",
    make_scenario("moderate"),
    '{"project_description": "Plateforme e-commerce en Python/Django vieille de 9.6 ans.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Modéré"}',
    dict(ok=True, needs_review=True),
))

# 12. composition junior/senior de l'équipe narrée dans risk_assessment -> flag
CASES.append((
    "FLAG - composition junior/senior narrée dans risk_assessment",
    make_scenario("moderate"),
    '{"project_description": "Plateforme e-commerce en Python/Django.", '
    '"analysis": "...", "recommendation": "Refactoring ciblé.", '
    '"phases": [{"phase": 1, "action": "...", "duration_days_range": "5-10 jours"}], '
    '"risk_assessment": "Équipe majoritairement junior, ce qui augmente le risque."}',
    dict(ok=True, needs_review=True),
))

passed, failed = 0, 0
for name, scenario, raw, expected in CASES:
    data, result = validate_output(raw, scenario)
    ok_match = result.ok == expected["ok"]
    review_match = ("needs_review" not in expected) or (result.needs_review == expected["needs_review"])
    status = "PASS" if (ok_match and review_match) else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    print(f"[{status}] {name} -> ok={result.ok} needs_review={result.needs_review} reason={result.reason}")

print(f"\n{passed} passés / {failed} échoués sur {len(CASES)} cas")
