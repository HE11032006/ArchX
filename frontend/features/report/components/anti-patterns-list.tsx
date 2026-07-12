import { Badge } from "@/shared/ui/badge";
import type { AntiPattern } from "@/shared/types/report";

interface AntiPatternsListProps {
  patterns: AntiPattern[];
}

export function AntiPatternsList({ patterns }: AntiPatternsListProps) {
  if (patterns.length === 0) {
    return (
      <div className="neon-card p-6">
        <p className="text-sm text-white/40">No anti-patterns detected.</p>
      </div>
    );
  }

  return (
    <div className="neon-card p-6">
      <div className="flex flex-wrap gap-2">
        {patterns.map((pattern, i) => (
          <Badge
            key={`${pattern.type}-${i}`}
            variant="outline"
            className="border-magenta/40 text-magenta"
            title={`${pattern.location} — ${pattern.detail}`}
          >
            {pattern.type}
          </Badge>
        ))}
      </div>
    </div>
  );
}
