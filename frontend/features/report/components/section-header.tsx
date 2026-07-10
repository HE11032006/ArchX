interface SectionHeaderProps {
  title: string;
  accent?: "cyan" | "magenta" | "muted";
}

const accentClass = {
  cyan: "text-cyan",
  magenta: "text-magenta",
  muted: "text-muted",
} as const;

export function SectionHeader({ title, accent = "cyan" }: SectionHeaderProps) {
  return <h2 className={`label-sm ${accentClass[accent]} mb-4`}>{title}</h2>;
}
