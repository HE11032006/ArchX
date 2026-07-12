import { Badge } from "@/shared/ui/badge";
import { getHealthDisplay } from "@/shared/lib/health-score";
import type { HealthBand, Report } from "@/shared/types/report";

import { ActionPlan } from "./action-plan";
import { AntiPatternsList } from "./anti-patterns-list";
import { CostPanel } from "./cost-panel";
import { DebtMap } from "./debt-map";
import { FeedbackPanel } from "./feedback-panel";
import { FixPromptsList } from "./fix-prompts-list";
import { MetricCard } from "./metric-card";
import { MigrationSimulator } from "./migration-simulator";
import { SectionHeader } from "./section-header";
import { StackPanel } from "./stack-panel";

const recommendationLabels = {
  refactoring: { label: "Refactoring", color: "var(--neon-cyan)" },
  migration: { label: "Migration", color: "var(--neon-magenta)" },
  maintain: { label: "Maintain", color: "#22c55e" },
} as const;

interface ReportViewProps {
  report: Report;
  repoUrl?: string;
  jobId: string;
}

export function ReportView({ report, repoUrl, jobId }: ReportViewProps) {
  const { metrics, recommendation, cost_analysis, health_band } = report;
  const health = getHealthDisplay(health_band as HealthBand, metrics);
  const rec =
    recommendationLabels[recommendation.recommendation] ??
    recommendationLabels.refactoring;

  return (
    <section className="mx-auto w-full max-w-6xl px-8 py-8">
      {/* Header */}
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
        {report.date && (
          <p className="mt-1 font-mono text-xs text-white/25">{report.date}</p>
        )}
      </div>

      {/* Health + Recommendation */}
      <div className="mb-8 grid gap-6 md:grid-cols-2">
        <div className="neon-card p-6">
          <span className="label-sm text-muted mb-3 block">Project Health</span>
          <div className="flex items-baseline gap-2">
            <span className="clash-bold text-5xl" style={{ color: health.color }}>
              {health.score}
            </span>
            <span className="text-white/35">/10</span>
          </div>
          <Badge
            variant="outline"
            className="mt-2 border-current capitalize"
            style={{ color: health.color }}
          >
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

      {/* Core metrics */}
      <SectionHeader title="Code Metrics" />
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label="Architecture"
          value={metrics.architecture_pattern}
        />
        <MetricCard
          label="Confidence"
          value={metrics.architecture_confidence}
          color="var(--neon-cyan)"
        />
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
        {metrics.total_functions != null && (
          <MetricCard label="Functions" value={metrics.total_functions} />
        )}
        {metrics.num_hotspots != null && (
          <MetricCard
            label="Git Hotspots"
            value={metrics.num_hotspots}
            color="var(--neon-magenta)"
          />
        )}
      </div>

      {/* Stack details */}
      <SectionHeader title="Stack & Infrastructure" accent="muted" />
      <div className="mb-8">
        <StackPanel metrics={metrics} />
      </div>

      {/* Anti-patterns */}
      {metrics.anti_patterns.length > 0 && (
        <div className="mb-8">
          <SectionHeader title="Anti-patterns" accent="magenta" />
          <AntiPatternsList patterns={metrics.anti_patterns} />
        </div>
      )}

      {/* Fix prompts */}
      <div className="mb-8">
        <SectionHeader title="Fix Prompts" accent="cyan" />
        <FixPromptsList prompts={report.fix_prompts ?? []} />
      </div>

      {/* Hotspots */}
      <div className="mb-8">
        <SectionHeader title="Risk Hotspots" />
        <DebtMap
          hotspots={metrics.complexity_hotspots ?? []}
          gitHotspots={metrics.git_hotspots}
        />
      </div>

      {/* AI Analysis */}
      <div className="neon-card mb-8 p-6">
        <SectionHeader title="AI Analysis" accent="magenta" />
        <p className="leading-relaxed text-white/60">{recommendation.analysis}</p>
      </div>

      {/* Feedback */}
      <FeedbackPanel jobId={jobId} />

      {/* Action plan */}
      <ActionPlan phases={recommendation.phases} />

      {/* Cost + Risk */}
      <div className="mb-8 grid gap-6 md:grid-cols-2">
        <CostPanel costAnalysis={cost_analysis} />
        <div className="neon-card p-6">
          <SectionHeader title="Risk Assessment" accent="muted" />
          <p className="leading-relaxed text-white/60">
            {recommendation.risk_assessment}
          </p>
        </div>
      </div>

      {/* Migration simulator */}
      <MigrationSimulator jobId={jobId} />
    </section>
  );
}
