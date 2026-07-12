export type HealthBand = "healthy" | "warning" | "critical";

export type RecommendationType = "refactoring" | "migration" | "maintain";

export interface ComplexityHotspot {
  file: string;
  max_complexity: number;
  num_functions: number;
  num_lines: number;
  num_imports: number;
}

export interface GitHotspot {
  file: string;
  total_changes_12mo: number;
  bugfix_changes_12mo: number;
  bugfix_ratio: number;
}

export interface AntiPattern {
  type: string;
  location: string;
  severity: "low" | "medium" | "high";
  detail: string;
}

export interface FixPrompt {
  type: string;
  location: string;
  prompt: string;
  fallback?: boolean;
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
  architecture_evidence?: string[];
  coupling_score: number;
  cohesion_score: number;
  avg_cyclomatic_complexity: number;
  test_coverage_estimate: number;
  top_hotspot_bugfix_ratio: number;
  num_hotspots?: number;
  files_analyzed: number;
  total_functions?: number;
  total_classes?: number;
  anti_patterns: AntiPattern[];
  complexity_hotspots: ComplexityHotspot[];
  git_hotspots?: GitHotspot[];
  dependencies: {
    total_dependencies: number;
    total_obsolete: number;
    has_dependency_files?: boolean;
    languages?: Record<string, { count: number; obsolete_count: number }>;
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
  fix_prompts?: FixPrompt[];
}

export interface MigrationTargets {
  current_stack: string;
  available_stacks: string[];
  suggested_stacks: string[];
}

export interface SimulateMigrationRequest {
  target_stack: string;
  team_size?: number;
  hourly_rate?: number;
  scale?: "small" | "medium" | "large";
}

export interface SimulateMigrationResult {
  current_stack: string;
  target_stack: string;
  migration_cost: number;
  current_cloud_cost: number;
  target_cloud_cost: number;
  monthly_savings: number;
  // null when there are no savings to pay back (FastAPI/Pydantic serialize
  // Python's float('inf') as null in JSON mode).
  payback_months: number | null;
  cost_confidence: string;
}

export interface HealthConfig {
  label: string;
  color: string;
  score: number;
}

export type HealthConfigMap = Record<HealthBand, HealthConfig>;
