"use client";

import { ReportView } from "@/features/report";
import { PipelineProgress, useScanJob } from "@/features/scan";

interface ReportPageClientProps {
  jobId: string;
}

export function ReportPageClient({ jobId }: ReportPageClientProps) {
  const { job, error, loading } = useScanJob(jobId);

  if (loading && !job) {
    return (
      <PipelineProgress
        currentStep={0}
        stepLabel="Queued"
        status="queued"
      />
    );
  }

  if (error && (!job || job.status === "failed")) {
    return (
      <PipelineProgress
        currentStep={job?.step ?? 0}
        stepLabel={error}
        status="failed"
      />
    );
  }

  if (!job) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-white/40">Job not found</p>
      </div>
    );
  }

  if (job.status !== "completed" || !job.report) {
    return (
      <PipelineProgress
        currentStep={job.step}
        stepLabel={job.step_label}
        status={job.status}
      />
    );
  }

  return <ReportView report={job.report} repoUrl={job.report.repo} />;
}
