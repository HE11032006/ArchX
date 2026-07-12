import { apiFetch } from "@/shared/api/client";
import type { FeedbackRequest, FeedbackResponse } from "@/shared/types/feedback";

export function submitFeedback(jobId: string, request: FeedbackRequest): Promise<FeedbackResponse> {
  return apiFetch<FeedbackResponse>(`/api/jobs/${jobId}/feedback`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
