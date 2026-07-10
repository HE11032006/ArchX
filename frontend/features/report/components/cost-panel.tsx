import type { CostAnalysis } from "@/shared/types/report";

interface CostPanelProps {
  costAnalysis: CostAnalysis;
}

export function CostPanel({ costAnalysis }: CostPanelProps) {
  const rows = [
    { label: "Migration cost", value: `${costAnalysis.migration_cost.toLocaleString()} €` },
    { label: "Monthly savings", value: `${costAnalysis.monthly_savings.toLocaleString()} €` },
    { label: "Payback", value: `${costAnalysis.payback_months} months` },
  ];

  return (
    <div className="neon-card p-6">
      <h2 className="label-sm text-muted mb-4">Cost Analysis</h2>
      {rows.map((row) => (
        <div key={row.label} className="mb-2 flex justify-between">
          <span className="text-sm text-white/45">{row.label}</span>
          <span className="font-mono text-sm text-neon-cyan">{row.value}</span>
        </div>
      ))}
    </div>
  );
}
