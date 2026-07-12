"use client";

import { useState } from "react";

import type { ComplexityHotspot, GitHotspot } from "@/shared/types/report";
import { cn } from "@/shared/lib/utils";

import { HotspotsTable } from "./hotspots-table";

interface DebtMapProps {
  hotspots: ComplexityHotspot[];
  gitHotspots?: GitHotspot[];
}

// Mêmes 3 couleurs que le reste de l'app (shared/lib/health-score.ts::BAND_CONFIG).
const SEVERITY_COLORS = {
  low: "#00F5FF",
  medium: "#F59E0B",
  high: "#FF00FF",
} as const;

type Severity = keyof typeof SEVERITY_COLORS;

// Mêmes seuils que le ratio de bugfix des bandes de santé (voir
// dataset_generation/scenario_axes.py::HEALTH_BANDS) quand un git hotspot
// correspondant existe ; sinon repli sur la complexité (seuil LONG_METHOD_COMPLEXITY
// côté backend, architect_insight/metrics/patterns.py).
function severityFor(hotspot: ComplexityHotspot, gitHotspot?: GitHotspot): Severity {
  if (gitHotspot) {
    if (gitHotspot.bugfix_ratio >= 0.5) return "high";
    if (gitHotspot.bugfix_ratio >= 0.2) return "medium";
    return "low";
  }
  if (hotspot.max_complexity >= 10) return "high";
  if (hotspot.max_complexity >= 5) return "medium";
  return "low";
}

function sizeSpan(num_lines: number, maxLines: number): number {
  if (maxLines <= 0) return 1;
  const ratio = num_lines / maxLines;
  if (ratio >= 0.66) return 3;
  if (ratio >= 0.33) return 2;
  return 1;
}

export function DebtMap({ hotspots, gitHotspots = [] }: DebtMapProps) {
  const [view, setView] = useState<"map" | "table">("map");

  if (view === "table") {
    return (
      <div>
        <ViewToggle view={view} onChange={setView} />
        <HotspotsTable complexityHotspots={hotspots} gitHotspots={gitHotspots} />
      </div>
    );
  }

  if (hotspots.length === 0) {
    return (
      <div className="neon-card p-4">
        <p className="text-sm text-white/40">No complexity hotspots found.</p>
      </div>
    );
  }

  const maxLines = Math.max(...hotspots.map((h) => h.num_lines), 1);
  const gitByFile = new Map(gitHotspots.map((h) => [h.file, h]));

  return (
    <div>
      <ViewToggle view={view} onChange={setView} />

      <div className="neon-card p-4">
        <div
          className="grid auto-rows-[64px] gap-2"
          style={{ gridTemplateColumns: "repeat(6, minmax(0, 1fr))" }}
        >
          {hotspots.map((h) => {
            const severity = severityFor(h, gitByFile.get(h.file));
            const span = sizeSpan(h.num_lines, maxLines);
            const color = SEVERITY_COLORS[severity];
            const bugfixRatio = gitByFile.get(h.file)?.bugfix_ratio;
            return (
              <div
                key={h.file}
                tabIndex={0}
                title={[
                  h.file,
                  `${h.num_lines} lines`,
                  `complexity ${h.max_complexity}`,
                  `${h.num_imports} imports`,
                  bugfixRatio != null ? `${(bugfixRatio * 100).toFixed(0)}% bugfix ratio` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
                className="flex flex-col justify-between overflow-hidden rounded-md border p-2 text-left transition-transform focus-visible:outline-none focus-visible:ring-2"
                style={{
                  gridColumn: `span ${span}`,
                  gridRow: `span ${span}`,
                  borderColor: color,
                  background: `color-mix(in srgb, ${color} 12%, transparent)`,
                }}
              >
                <span className="truncate font-mono text-[0.65rem] text-white/60">
                  {h.file}
                </span>
                <span className="font-mono text-sm font-semibold" style={{ color }}>
                  {h.max_complexity}
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-white/8 pt-3">
          {(Object.keys(SEVERITY_COLORS) as Severity[]).map((severity) => (
            <div key={severity} className="flex items-center gap-1.5">
              <span
                className="inline-block size-2.5 rounded-full"
                style={{ background: SEVERITY_COLORS[severity] }}
              />
              <span className="text-xs text-white/45 capitalize">{severity} risk</span>
            </div>
          ))}
          <span className="text-xs text-white/30">Tile size = file length (LOC)</span>
        </div>
      </div>
    </div>
  );
}

function ViewToggle({
  view,
  onChange,
}: {
  view: "map" | "table";
  onChange: (v: "map" | "table") => void;
}) {
  return (
    <div className="mb-3 flex gap-2">
      {(["map", "table"] as const).map((v) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          className={cn(
            "rounded-lg border px-2.5 py-1 text-xs capitalize transition-colors",
            view === v
              ? "border-current text-neon-cyan"
              : "border-white/10 text-white/45 hover:text-white/70",
          )}
        >
          {v} view
        </button>
      ))}
    </div>
  );
}
