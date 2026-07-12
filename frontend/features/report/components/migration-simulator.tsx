"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import type { MigrationTargets, SimulateMigrationResult } from "@/shared/types/report";

import { getMigrationTargets, simulateMigration } from "../api/migration";

interface MigrationSimulatorProps {
  jobId: string;
}

export function MigrationSimulator({ jobId }: MigrationSimulatorProps) {
  const [targets, setTargets] = useState<MigrationTargets | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [result, setResult] = useState<SimulateMigrationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMigrationTargets(jobId)
      .then((t) => {
        setTargets(t);
        setSelected(t.suggested_stacks[0] ?? t.available_stacks[0] ?? "");
      })
      .catch(() => setError("Could not load migration targets."));
  }, [jobId]);

  async function handleSimulate() {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const res = await simulateMigration(jobId, { target_stack: selected });
      setResult(res);
    } catch {
      setError("Simulation failed — please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (!targets) {
    return null;
  }

  return (
    <div className="neon-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="label-sm text-muted">Migration Simulator</h2>
        <span className="font-mono text-xs text-white/35">
          current: {targets.current_stack}
        </span>
      </div>

      <p className="mb-3 text-sm text-white/45">
        Deterministic estimate, computed the same way as the report&apos;s cost
        analysis — no model call. Pick any target stack to see the numbers.
      </p>

      <div className="mb-4 flex flex-wrap gap-2">
        {targets.available_stacks.map((stack) => (
          <button
            key={stack}
            type="button"
            onClick={() => setSelected(stack)}
            className={`rounded-lg border px-2.5 py-1 text-xs transition-colors ${
              selected === stack
                ? "border-current text-neon-cyan"
                : "border-white/10 text-white/45 hover:text-white/70"
            }`}
          >
            {stack}
            {targets.suggested_stacks.includes(stack) && (
              <span className="ml-1 text-white/30">★</span>
            )}
          </button>
        ))}
      </div>

      <Button onClick={handleSimulate} disabled={loading || !selected}>
        {loading ? "Simulating..." : `Simulate migration to ${selected || "..."}`}
      </Button>

      {error && <p className="mt-2 text-sm text-neon-magenta">{error}</p>}

      {result && (
        <div className="mt-5 border-t border-white/10 pt-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm text-white/60">
              {result.current_stack} → {result.target_stack}
            </span>
            <Badge variant="outline" className="text-xs capitalize">
              {result.cost_confidence} confidence
            </Badge>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Row label="Migration cost" value={`${result.migration_cost.toLocaleString()} €`} />
            <Row
              label="Cloud cost / month"
              value={`${result.current_cloud_cost.toLocaleString()} € → ${result.target_cloud_cost.toLocaleString()} €`}
            />
            <Row label="Monthly savings" value={`${result.monthly_savings.toLocaleString()} €`} />
            <Row
              label="Payback period"
              value={
                result.payback_months == null
                  ? "N/A (no savings)"
                  : `${result.payback_months} months`
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-sm text-white/45">{label}</span>
      <span className="font-mono text-sm text-neon-cyan">{value}</span>
    </div>
  );
}
