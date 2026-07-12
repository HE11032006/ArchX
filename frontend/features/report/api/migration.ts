import { apiFetch } from "@/shared/api/client";
import type {
  MigrationTargets,
  SimulateMigrationRequest,
  SimulateMigrationResult,
} from "@/shared/types/report";

export function getMigrationTargets(jobId: string): Promise<MigrationTargets> {
  return apiFetch<MigrationTargets>(`/api/jobs/${jobId}/migration-targets`);
}

export function simulateMigration(
  jobId: string,
  request: SimulateMigrationRequest,
): Promise<SimulateMigrationResult> {
  return apiFetch<SimulateMigrationResult>(`/api/jobs/${jobId}/simulate-migration`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
