import type { HealthBand, Metrics } from "@/shared/types/report";

const BAND_CONFIG: Record<HealthBand, { label: string; color: string }> = {
  healthy: { label: "Healthy", color: "#00F5FF" },
  warning: { label: "Warning", color: "#F59E0B" },
  critical: { label: "Critical", color: "#FF00FF" },
};

export function computeHealthScore(metrics: Metrics): number {
  let score = 10;

  if (metrics.coupling_score > 7) score -= 2;
  else if (metrics.coupling_score > 4) score -= 1;

  if (metrics.cohesion_score < 4) score -= 2;
  else if (metrics.cohesion_score < 6) score -= 1;

  if (metrics.test_coverage_estimate < 40) score -= 2;
  else if (metrics.test_coverage_estimate < 60) score -= 1;

  if (metrics.avg_cyclomatic_complexity > 8) score -= 1;

  const antiCount = metrics.anti_patterns?.length ?? 0;
  if (antiCount > 5) score -= 1;
  else if (antiCount > 2) score -= 0.5;

  return Math.max(1, Math.round(score * 10) / 10);
}

export function getHealthDisplay(band: HealthBand, metrics: Metrics) {
  const config = BAND_CONFIG[band] ?? BAND_CONFIG.warning;
  return {
    ...config,
    score: computeHealthScore(metrics),
  };
}
