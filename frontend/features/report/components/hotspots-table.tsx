import type { ComplexityHotspot, GitHotspot } from "@/shared/types/report";

interface HotspotsTableProps {
  complexityHotspots: ComplexityHotspot[];
  gitHotspots?: GitHotspot[];
}

function TableHeader({ cols }: { cols: string[] }) {
  return (
    <thead>
      <tr className="border-b border-white/8">
        {cols.map((col) => (
          <th
            key={col}
            className="label-sm text-muted px-3 py-2 text-left font-normal"
          >
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export function HotspotsTable({ complexityHotspots, gitHotspots = [] }: HotspotsTableProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="neon-card overflow-hidden">
        <div className="border-b border-white/8 px-4 py-3">
          <span className="label-sm text-cyan">Complexity Hotspots</span>
        </div>
        {complexityHotspots.length === 0 ? (
          <p className="p-4 text-sm text-white/40">No complexity hotspots found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <TableHeader cols={["File", "Complexity", "Functions"]} />
              <tbody>
                {complexityHotspots.slice(0, 8).map((h) => (
                  <tr key={h.file} className="border-b border-white/5">
                    <td className="font-mono px-3 py-2 text-xs text-white/70">{h.file}</td>
                    <td className="px-3 py-2 text-neon-magenta">{h.max_complexity}</td>
                    <td className="px-3 py-2 text-white/50">{h.num_functions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="neon-card overflow-hidden">
        <div className="border-b border-white/8 px-4 py-3">
          <span className="label-sm text-magenta">Git Hotspots (12 mo)</span>
        </div>
        {gitHotspots.length === 0 ? (
          <p className="p-4 text-sm text-white/40">No git history available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <TableHeader cols={["File", "Changes", "Bugfix %"]} />
              <tbody>
                {gitHotspots.slice(0, 8).map((h) => (
                  <tr key={h.file} className="border-b border-white/5">
                    <td className="font-mono px-3 py-2 text-xs text-white/70">{h.file}</td>
                    <td className="px-3 py-2 text-white/50">{h.total_changes_12mo}</td>
                    <td className="px-3 py-2 text-neon-cyan">
                      {(h.bugfix_ratio * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
