import { apiFetch } from "@/shared/api/client";
import type { AnalyzeRequest, AnalyzeResponse, DemoProject, JobResponse } from "@/shared/types/job";

export function startAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function getJob(jobId: string): Promise<JobResponse> {
  return apiFetch<JobResponse>(`/api/jobs/${jobId}`);
}

export function getDemoProjects(): Promise<DemoProject[]> {
  return apiFetch<DemoProject[]>("/api/demo-projects");
}
