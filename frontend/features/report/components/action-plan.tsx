import type { Phase } from "@/shared/types/report";

interface ActionPlanProps {
  phases: Phase[];
}

export function ActionPlan({ phases }: ActionPlanProps) {
  if (phases.length === 0) return null;

  return (
    <div className="mb-8">
      <h2 className="label-sm text-cyan mb-4">Action Plan</h2>
      <div className="flex flex-col gap-3">
        {phases.map((phase) => (
          <div
            key={phase.phase}
            className="neon-card flex items-start gap-4 px-5 py-4"
          >
            <span className="clash-bold text-cyan min-w-8 text-xl">{phase.phase}</span>
            <div>
              <p className="mb-1 text-white">{phase.action}</p>
              <span className="font-mono text-[10px] text-white/35">
                {phase.duration_days_range ?? `${phase.duration_days} days`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
