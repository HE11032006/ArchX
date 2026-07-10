import type { HealthConfigMap, Report } from "@/shared/types/report";

export const mockReport: Report = {
  repo: "demo_projects/django_app",
  date: "2026-07-06",
  metrics: {
    architecture_pattern: "Django (MVT)",
    architecture_confidence: "high",
    coupling_score: 1.8,
    cohesion_score: 7.1,
    avg_cyclomatic_complexity: 3.2,
    test_coverage_estimate: 66.6,
    top_hotspot_bugfix_ratio: 0.12,
    files_analyzed: 1402,
    anti_patterns: ["God Class", "Long Method", "Circular Dependency"],
    complexity_hotspots: [
      { file: "core/views.py", max_complexity: 18, num_functions: 12 },
      { file: "api/serializers.py", max_complexity: 11, num_functions: 8 },
      { file: "users/models.py", max_complexity: 9, num_functions: 6 },
    ],
    dependencies: {
      total_dependencies: 24,
      total_obsolete: 5,
    },
    database: {
      detected_databases: ["postgresql"],
      detected_orms: ["django_orm"],
      migration_count: 48,
      complexity: "medium",
    },
    tests: {
      total_test_files: 18,
      total_test_functions: 142,
      test_ratio: 0.28,
      coverage_estimate: "medium",
      frameworks: ["pytest", "django-test"],
    },
    performance: {
      performance_score: "medium",
      endpoints_count: 34,
      external_calls_detected: 8,
      potential_n_plus_1_hotspots: 4,
    },
  },
  recommendation: {
    project_description:
      "Plateforme e-commerce mature (4 ans) avec une stack Python/Django/PostgreSQL. L'équipe est mixte (60% juniors). Dette technique modérée identifiée.",
    analysis:
      "Les métriques techniques indiquent une architecture solide mais perfectible : faible couplage (1.8/10), bonne cohésion (7.1/10) et complexité cyclomatique raisonnable. La couverture de tests (66.6%) est perfectible. 4 hotspots N+1 détectés.",
    recommendation: "refactoring",
    phases: [
      {
        phase: 1,
        action: "Réduire la dette technique — refactoring ciblé des hotspots N+1",
        duration_days_range: "10-15 jours",
      },
      {
        phase: 2,
        action: "Améliorer la couverture de tests (cible : 80%)",
        duration_days_range: "15-20 jours",
      },
      {
        phase: 3,
        action: "Migration Progressive vers microservices sur les modules les plus chargés",
        duration_days_range: "30-45 jours",
      },
    ],
    risk_assessment:
      "Modéré — Risque principal sur les dépendances externes (paiement, logistique).",
  },
  cost_analysis: {
    migration_cost: 42000,
    current_cloud_cost: 2450,
    target_cloud_cost: 1800,
    monthly_savings: 650,
    payback_months: 64.6,
    cost_confidence: "high",
  },
  health_band: "warning",
};

export const healthConfig: HealthConfigMap = {
  healthy: { label: "Healthy", color: "#00F5FF", score: 8.5 },
  warning: { label: "Warning", color: "#F59E0B", score: 6.2 },
  critical: { label: "Critical", color: "#FF00FF", score: 3.1 },
};
