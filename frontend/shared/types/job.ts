import type { Report } from "./report";

export type JobStatus =
  | "queued"
  | "collecting"
  | "building_prompt"
  | "inferring"
  | "computing_costs"
  | "completed"
  | "failed";

export interface AnalyzeRequest {
  repo: string;
  language?: "fr" | "en";
  team_size?: number;
  hourly_rate?: number;
}

export interface AnalyzeResponse {
  job_id: string;
}

export interface JobResponse {
  id: string;
  status: JobStatus;
  step: number;
  step_label: string;
  error: string | null;
  report: Report | null;
}

export interface DemoProject {
  slug: string;
  path: string;
  label: string;
}
