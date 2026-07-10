import { Badge } from "@/shared/ui/badge";
import { healthConfig } from "@/shared/data/mockReport";
import type { HealthBand } from "@/shared/types/report";
import type { Report } from "@/shared/types/report";

import { ActionPlan } from "./action-plan";
import { CostPanel } from "./cost-panel";
import { MetricCard } from "./metric-card";

const recommendationLabels = {
  refactoring: { label: "Refactoring", color: "var(--neon-cyan)" },
  migration: { label: "Migration", color: "var(--neon-magenta)" },
  maintain: { label: "Maintain", color: "#22c55e" },
} as const;

interface ReportViewProps {
  report: Report;
  repoUrl?: string;
}

export function ReportView({ report, repoUrl }: ReportViewProps) {
  const { metrics, recommendation, cost_analysis, health_band } = report;
  const health = healthConfig[health_band as HealthBand] ?? healthConfig.warning;
  const rec =
    recommendationLabels[recommendation.recommendation] ??
    recommendationLabels.refactoring;

  return (
    <section className="mx-auto w-full max-w-6xl px-8 py-8">
      <div className="mb-10">
        <div className="status-badge mb-4 w-fit">
          <span className="label-sm text-cyan">Analysis Complete</span>
          <span className="status-dot" />
        </div>
        <h1 className="clash-bold mb-2 text-[clamp(2rem,4vw,3rem)]">
          Architecture Report
        </h1>
        <p className="font-mono text-sm text-white/40">
          {repoUrl ?? report.repo}
        </p>
      </div>

      <div className="mb-8 grid gap-6 md:grid-cols-2">
        <div className="neon-card p-6">
          <span className="label-sm text-muted mb-3 block">Project Health</span>
          <div className="flex items-baseline gap-2">
            <span className="clash-bold text-5xl" style={{ color: health.color }}>
              {health.score}
            </span>
            <span className="text-white/35">/10</span>
          </div>
          <Badge variant="outline" className="mt-2 border-current" style={{ color: health.color }}>
            {health.label}
          </Badge>
        </div>

        <div className="neon-card p-6">
          <span className="label-sm text-muted mb-3 block">AI Recommendation</span>
          <span
            className="clash-bold mb-3 block text-3xl"
            style={{ color: rec.color }}
          >
            {rec.label}
          </span>
          <p className="text-sm leading-relaxed text-white/55">
            {recommendation.project_description}
          </p>
        </div>
      </div>

      <h2 className="label-sm text-cyan mb-4">Code Metrics</h2>
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard label="Architecture" value={metrics.architecture_pattern} />
        <MetricCard
          label="Coupling"
          value={metrics.coupling_score}
          suffix="/10"
          color="var(--neon-cyan)"
        />
        <MetricCard
          label="Cohesion"
          value={metrics.cohesion_score}
          suffix="/10"
          color="var(--neon-cyan)"
        />
        <MetricCard label="Complexity" value={metrics.avg_cyclomatic_complexity} />
        <MetricCard
          label="Test Coverage"
          value={`${metrics.test_coverage_estimate}%`}
          color="var(--neon-magenta)"
        />
        <MetricCard label="Files Analyzed" value={metrics.files_analyzed} />
      </div>

      <div className="neon-card mb-8 p-6">
        <h2 className="label-sm text-magenta mb-3">Analysis</h2>
        <p className="leading-relaxed text-white/60">{recommendation.analysis}</p>
      </div>

      <ActionPlan phases={recommendation.phases} />

      <div className="grid gap-6 md:grid-cols-2">
        <CostPanel costAnalysis={cost_analysis} />
        <div className="neon-card p-6">
          <h2 className="label-sm text-muted mb-4">Risk Assessment</h2>
          <p className="leading-relaxed text-white/60">
            {recommendation.risk_assessment}
          </p>
        </div>
      </div>
    </section>
  );
}
