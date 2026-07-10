"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getDemoProjects, startAnalysis } from "@/features/scan/api/analyze";
import { ApiError } from "@/shared/api/client";
import type { DemoProject } from "@/shared/types/job";

export function ScanForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoProjects, setDemoProjects] = useState<DemoProject[]>([]);

  useEffect(() => {
    getDemoProjects()
      .then(setDemoProjects)
      .catch(() => setDemoProjects([]));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setScanning(true);
    setError(null);

    try {
      const { job_id } = await startAnalysis({ repo: url.trim(), language: "fr" });
      router.push(`/report/${job_id}`);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Failed to start analysis";
      setError(message);
      setScanning(false);
    }
  };

  const selectDemo = (slug: string) => {
    setUrl(slug);
    setError(null);
  };

  return (
    <div className="flex flex-col gap-10">
      <div className="status-badge w-fit">
        <span className="label-sm text-cyan">Status: Analysis Core Active</span>
        <span className="status-dot" />
      </div>

      <h1
        className="clash-bold tracking-tighter text-white"
        style={{ fontSize: "clamp(56px, 8vw, 100px)", lineHeight: 0.85 }}
      >
        THE <span className="text-sharp-gradient">ORACLE</span>
        <br />
        OF YOUR
        <br />
        <span style={{ color: "var(--neon-magenta)" }}>STACK.</span>
      </h1>

      <p className="max-w-lg border-l border-white/20 pl-6 text-[1.1rem] leading-relaxed font-light text-white/55">
        Intelligence artificielle avancée pour l&apos;analyse de dette technique, les chemins
        de migration et l&apos;architecture logicielle prédictive — propulsée par Gemma fine-tuné
        sur AMD MI300X.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="group relative max-w-xl">
          <div
            className="pointer-events-none absolute -inset-1 opacity-15 blur-sm transition-opacity duration-400"
            style={{
              background: "linear-gradient(to right, var(--neon-cyan), var(--neon-magenta))",
            }}
          />
          <div className="relative flex">
            <div className="cyber-input-wrap flex flex-1 items-center px-4">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="2"
                className="mr-3 shrink-0"
              >
                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
              </svg>
              <input
                className="cyber-input py-4"
                type="text"
                placeholder="https://github.com/org/repo or django_app"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={scanning}
              />
            </div>
            <button
              type="submit"
              disabled={scanning}
              className="cyber-btn cyber-btn-primary shrink-0 px-8 py-4 text-[0.8rem]"
              style={{ opacity: scanning ? 0.7 : 1 }}
            >
              {scanning ? "⟳ Scanning..." : "Run Scan ▶"}
            </button>
          </div>
        </div>

        {demoProjects.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="label-sm text-muted mr-1 self-center">Demo:</span>
            {demoProjects.map((project) => (
              <button
                key={project.slug}
                type="button"
                onClick={() => selectDemo(project.slug)}
                className="rounded border border-white/10 px-3 py-1 font-mono text-xs text-white/50 transition-colors hover:border-neon-cyan hover:text-neon-cyan"
              >
                {project.label}
              </button>
            ))}
          </div>
        )}

        {error && (
          <p className="mt-3 font-mono text-xs text-magenta">{error}</p>
        )}
      </form>

      <div className="flex items-center gap-8 pt-2">
        {[
          { value: "3", label: "Demo Projects" },
          { value: "Real", label: "Collector Metrics", color: "var(--neon-cyan)" },
          { value: "AI", label: "Gemma Powered", color: "var(--neon-magenta)" },
        ].map((stat, i) => (
          <div key={stat.label} className="flex items-center gap-8">
            {i > 0 && <div className="h-10 w-px bg-white/10" />}
            <div>
              <div className="clash-bold text-2xl" style={{ color: stat.color ?? "#fff" }}>
                {stat.value}
              </div>
              <div className="label-sm text-muted">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
