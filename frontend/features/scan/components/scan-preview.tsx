export function ScanPreview() {
  return (
    <div className="relative hidden lg:block">
      <div
        className="absolute inset-0 rounded-full blur-[100px]"
        style={{ background: "rgba(0,245,255,0.1)" }}
      />
      <div className="neon-card relative overflow-hidden p-6">
        <div className="mb-6 flex items-center justify-between border-b border-white/8 pb-4">
          <span className="font-mono text-[10px] tracking-widest text-neon-cyan uppercase">
            Process: Migration Simulation
          </span>
          <div className="flex gap-1.5">
            {["rgba(255,255,255,0.15)", "rgba(255,0,255,0.4)", "rgba(0,245,255,0.4)"].map(
              (c, i) => (
                <div key={i} className="h-2 w-2 rounded-full" style={{ background: c }} />
              ),
            )}
          </div>
        </div>

        <div className="flex flex-col gap-6">
          {[
            { label: "Complexity Coefficient", value: 84.2, color: "var(--neon-magenta)" },
            { label: "Test Coverage", value: 66.6, color: "var(--neon-cyan)" },
          ].map((bar) => (
            <div key={bar.label} className="flex flex-col gap-1.5">
              <div className="font-mono flex justify-between">
                <span className="text-[10px] text-white/40 uppercase">{bar.label}</span>
                <span className="text-[10px]" style={{ color: bar.color }}>
                  {bar.value}%
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${bar.value}%`,
                    background: bar.color,
                    boxShadow: `0 0 8px ${bar.color}`,
                  }}
                />
              </div>
            </div>
          ))}

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Project Health", value: "7.4", suffix: "/10", color: "var(--neon-cyan)" },
              { label: "Migration ROI", value: "2.4x", color: "var(--neon-magenta)" },
            ].map((kpi) => (
              <div
                key={kpi.label}
                className="border border-white/8 bg-white/4 p-4"
              >
                <span className="label-sm mb-2 block" style={{ color: kpi.color }}>
                  {kpi.label}
                </span>
                <span className="clash-bold text-2xl">
                  {kpi.value}
                  {kpi.suffix && (
                    <span className="ml-1 text-xs text-white/35">{kpi.suffix}</span>
                  )}
                </span>
              </div>
            ))}
          </div>

          <div className="border-t border-white/8 pt-4">
            {[
              { icon: "cyan", text: "Analyzed: 1,402 files across 38 modules" },
              { icon: "cyan", text: "Detected: Python / Django / PostgreSQL" },
              { icon: "cyan", text: "Anti-patterns: 3 identified" },
              { icon: "magenta", text: "Recommend: Refactoring + Microservices...", pulse: true },
            ].map((line, i) => (
              <div
                key={i}
                className={`terminal-line flex items-center gap-2 ${line.pulse ? "animate-pulse" : ""}`}
              >
                <span style={{ color: line.icon === "cyan" ? "var(--neon-cyan)" : "var(--neon-magenta)" }}>
                  &gt;
                </span>
                <span style={{ color: line.pulse ? "rgba(255,255,255,0.5)" : "inherit" }}>
                  {line.text}
                </span>
                {line.pulse && (
                  <span className="cursor-blink text-magenta">█</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
