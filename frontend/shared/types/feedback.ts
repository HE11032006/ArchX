export type FeedbackRating = "up" | "down";

export interface FeedbackRequest {
  rating: FeedbackRating;
  correction?: string | null;
}

export interface FeedbackResponse {
  ok: boolean;
}
