interface MetricCardProps {
  label: string;
  value: string | number;
  suffix?: string;
  color?: string;
}

export function MetricCard({ label, value, suffix, color }: MetricCardProps) {
  return (
    <div className="neon-card p-5">
      <span className="label-sm text-muted mb-2 block">{label}</span>
      <span className="clash-bold text-[1.75rem]" style={{ color: color ?? "#fff" }}>
        {value}
        {suffix && (
          <span className="ml-1 text-sm text-white/35">{suffix}</span>
        )}
      </span>
    </div>
  );
}
