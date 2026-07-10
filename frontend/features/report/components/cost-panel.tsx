import type { CostAnalysis } from "@/shared/types/report";
import { Badge } from "@/shared/ui/badge";

interface CostPanelProps {
  costAnalysis: CostAnalysis;
}

function CostBar({
  label,
  current,
  target,
  format,
}: {
  label: string;
  current: number;
  target: number;
  format: (n: number) => string;
}) {
  const max = Math.max(current, target, 1);
  const currentPct = (current / max) * 100;
  const targetPct = (target / max) * 100;

  return (
    <div className="mb-4">
      <div className="mb-2 flex justify-between text-sm">
        <span className="text-white/45">{label}</span>
        <span className="font-mono text-white/60">
          {format(current)} → {format(target)}
        </span>
      </div>
      <div className="relative h-2 bg-white/5">
        <div
          className="absolute top-0 left-0 h-full bg-white/20"
          style={{ width: `${currentPct}%` }}
        />
        <div
          className="absolute top-0 left-0 h-full"
          style={{
            width: `${targetPct}%`,
            background: "var(--neon-cyan)",
            boxShadow: "0 0 6px var(--neon-cyan)",
          }}
        />
      </div>
    </div>
  );
}

export function CostPanel({ costAnalysis }: CostPanelProps) {
  const rows = [
    { label: "Migration cost", value: `${costAnalysis.migration_cost.toLocaleString()} €` },
    { label: "Monthly savings", value: `${costAnalysis.monthly_savings.toLocaleString()} €` },
    { label: "Payback period", value: `${costAnalysis.payback_months} months` },
  ];

  return (
    <div className="neon-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="label-sm text-muted">Cost Analysis</h2>
        <Badge variant="outline" className="text-xs capitalize">
          {costAnalysis.cost_confidence} confidence
        </Badge>
      </div>

      <CostBar
        label="Cloud cost / month"
        current={costAnalysis.current_cloud_cost}
        target={costAnalysis.target_cloud_cost}
        format={(n) => `${n.toLocaleString()} €`}
      />

      {rows.map((row) => (
        <div key={row.label} className="mb-2 flex justify-between">
          <span className="text-sm text-white/45">{row.label}</span>
          <span className="font-mono text-sm text-neon-cyan">{row.value}</span>
        </div>
      ))}
    </div>
  );
}
