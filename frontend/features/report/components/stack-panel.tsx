import type { Metrics } from "@/shared/types/report";

interface StackPanelProps {
  metrics: Metrics;
}

function DetailRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between border-b border-white/5 py-2 last:border-0">
      <span className="text-sm text-white/45">{label}</span>
      <span className="font-mono text-sm text-white/80">{value}</span>
    </div>
  );
}

function SubCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="neon-card p-5">
      <span className="label-sm text-muted mb-3 block">{title}</span>
      {children}
    </div>
  );
}

export function StackPanel({ metrics }: StackPanelProps) {
  const { database, dependencies, tests, performance } = metrics;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <SubCard title="Database">
        <DetailRow
          label="Databases"
          value={database.detected_databases.join(", ") || "—"}
        />
        <DetailRow label="ORMs" value={database.detected_orms.join(", ") || "—"} />
        <DetailRow label="Migrations" value={database.migration_count} />
        <DetailRow label="Complexity" value={database.complexity} />
      </SubCard>

      <SubCard title="Dependencies">
        <DetailRow label="Total" value={dependencies.total_dependencies} />
        <DetailRow
          label="Obsolete"
          value={dependencies.total_obsolete}
        />
        {dependencies.languages &&
          Object.entries(dependencies.languages).map(([lang, info]) => (
            <DetailRow
              key={lang}
              label={lang}
              value={`${info.count} deps (${info.obsolete_count} obsolete)`}
            />
          ))}
      </SubCard>

      <SubCard title="Tests">
        <DetailRow label="Test files" value={tests.total_test_files} />
        <DetailRow label="Test functions" value={tests.total_test_functions} />
        <DetailRow label="Test ratio" value={`${(tests.test_ratio * 100).toFixed(0)}%`} />
        <DetailRow label="Frameworks" value={tests.frameworks.join(", ") || "—"} />
        <DetailRow label="Coverage est." value={tests.coverage_estimate} />
      </SubCard>

      <SubCard title="Performance">
        <DetailRow label="Score" value={performance.performance_score} />
        <DetailRow label="Endpoints" value={performance.endpoints_count} />
        <DetailRow label="External calls" value={performance.external_calls_detected} />
        <DetailRow label="N+1 hotspots" value={performance.potential_n_plus_1_hotspots} />
      </SubCard>
    </div>
  );
}
