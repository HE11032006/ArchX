import type { JobStatus } from "@/shared/types/job";

const STEPS: { step: number; label: string; status: JobStatus }[] = [
  { step: 1, label: "Collecting metrics", status: "collecting" },
  { step: 2, label: "Building prompt", status: "building_prompt" },
  { step: 3, label: "Generating recommendation", status: "inferring" },
  { step: 4, label: "Computing costs", status: "computing_costs" },
  { step: 5, label: "Finalizing report", status: "completed" },
];

interface PipelineProgressProps {
  currentStep: number;
  stepLabel: string;
  status: JobStatus;
}

export function PipelineProgress({ currentStep, stepLabel, status }: PipelineProgressProps) {
  const isFailed = status === "failed";

  return (
    <section className="mx-auto flex min-h-[calc(100vh-200px)] w-full max-w-2xl flex-col items-center justify-center px-8 py-16">
      <div className="status-badge mb-8 w-fit">
        <span className="label-sm text-cyan">
          {isFailed ? "Analysis Failed" : "Analysis In Progress"}
        </span>
        <span className={`status-dot ${isFailed ? "bg-magenta" : ""}`} />
      </div>

      <h1 className="clash-bold mb-2 text-center text-3xl">
        {isFailed ? "Something went wrong" : "Scanning your stack..."}
      </h1>
      <p className="mb-10 text-center font-mono text-sm text-white/40">
        {isFailed ? stepLabel : stepLabel}
      </p>

      <div className="neon-card w-full p-6">
        <div className="flex flex-col gap-4">
          {STEPS.map((step) => {
            const done = !isFailed && currentStep > step.step;
            const active = !isFailed && currentStep === step.step;
            const pending = !done && !active;

            return (
              <div key={step.step} className="flex items-center gap-4">
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center font-mono text-xs"
                  style={{
                    background: done
                      ? "var(--neon-cyan)"
                      : active
                        ? "rgba(0,245,255,0.2)"
                        : "rgba(255,255,255,0.05)",
                    color: done ? "#000" : active ? "var(--neon-cyan)" : "rgba(255,255,255,0.3)",
                    border: active ? "1px solid var(--neon-cyan)" : "1px solid transparent",
                  }}
                >
                  {done ? "✓" : step.step}
                </div>
                <div className="flex-1">
                  <p
                    className="text-sm"
                    style={{
                      color: pending ? "rgba(255,255,255,0.3)" : "#fff",
                    }}
                  >
                    {step.label}
                  </p>
                  {active && (
                    <div className="progress-track mt-2">
                      <div
                        className="progress-fill"
                        style={{
                          width: "60%",
                          background: "var(--neon-cyan)",
                          boxShadow: "0 0 8px var(--neon-cyan)",
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
