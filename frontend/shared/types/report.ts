export type HealthBand = "healthy" | "warning" | "critical";

export type RecommendationType = "refactoring" | "migration" | "maintain";

export interface ComplexityHotspot {
  file: string;
  max_complexity: number;
  num_functions: number;
}

export interface Phase {
  phase: number;
  action: string;
  duration_days?: number;
  duration_days_range?: string;
}

export interface Metrics {
  architecture_pattern: string;
  architecture_confidence: string;
  coupling_score: number;
  cohesion_score: number;
  avg_cyclomatic_complexity: number;
  test_coverage_estimate: number;
  top_hotspot_bugfix_ratio: number;
  files_analyzed: number;
  anti_patterns: string[];
  complexity_hotspots: ComplexityHotspot[];
  dependencies: {
    total_dependencies: number;
    total_obsolete: number;
  };
  database: {
    detected_databases: string[];
    detected_orms: string[];
    migration_count: number;
    complexity: string;
  };
  tests: {
    total_test_files: number;
    total_test_functions: number;
    test_ratio: number;
    coverage_estimate: string;
    frameworks: string[];
  };
  performance: {
    performance_score: string;
    endpoints_count: number;
    external_calls_detected: number;
    potential_n_plus_1_hotspots: number;
  };
}

export interface Recommendation {
  project_description: string;
  analysis: string;
  recommendation: RecommendationType;
  phases: Phase[];
  risk_assessment: string;
}

export interface CostAnalysis {
  migration_cost: number;
  current_cloud_cost: number;
  target_cloud_cost: number;
  monthly_savings: number;
  payback_months: number;
  cost_confidence: string;
}

export interface Report {
  repo: string;
  date: string;
  metrics: Metrics;
  recommendation: Recommendation;
  cost_analysis: CostAnalysis;
  health_band: HealthBand;
}

export interface HealthConfig {
  label: string;
  color: string;
  score: number;
}

export type HealthConfigMap = Record<HealthBand, HealthConfig>;
