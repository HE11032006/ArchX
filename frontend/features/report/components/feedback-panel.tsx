"use client";

import { useState } from "react";

import { Button } from "@/shared/ui/button";
import { cn } from "@/shared/lib/utils";
import type { FeedbackRating } from "@/shared/types/feedback";

import { submitFeedback } from "../api/feedback";

interface FeedbackPanelProps {
  jobId: string;
}

export function FeedbackPanel({ jobId }: FeedbackPanelProps) {
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [correction, setCorrection] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!rating) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback(jobId, { rating, correction: correction.trim() || null });
      setSubmitted(true);
    } catch {
      setError("Could not submit feedback — please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="neon-card mb-8 p-6">
        <p className="text-sm text-white/60">
          Thanks — this helps train the next version of the model.
        </p>
      </div>
    );
  }

  return (
    <div className="neon-card mb-8 p-6">
      <span className="label-sm text-muted mb-3 block">Was this recommendation useful?</span>
      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={() => setRating("up")}
          aria-pressed={rating === "up"}
          className={cn(
            "rounded-lg border px-4 py-2 text-lg transition-colors",
            rating === "up"
              ? "border-current text-neon-cyan"
              : "border-white/10 text-white/40 hover:text-white/70",
          )}
        >
          👍
        </button>
        <button
          type="button"
          onClick={() => setRating("down")}
          aria-pressed={rating === "down"}
          className={cn(
            "rounded-lg border px-4 py-2 text-lg transition-colors",
            rating === "down"
              ? "border-current text-neon-magenta"
              : "border-white/10 text-white/40 hover:text-white/70",
          )}
        >
          👎
        </button>
      </div>

      {rating && (
        <>
          <textarea
            value={correction}
            onChange={(e) => setCorrection(e.target.value)}
            placeholder="What would you correct about this recommendation? (optional)"
            rows={3}
            maxLength={4000}
            className="mb-3 w-full rounded-lg border border-white/10 bg-transparent p-2.5 text-sm text-white/80 placeholder:text-white/30 focus-visible:border-white/30 focus-visible:outline-none"
          />
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Submitting..." : "Submit feedback"}
          </Button>
          {error && <p className="mt-2 text-sm text-neon-magenta">{error}</p>}
        </>
      )}
    </div>
  );
}
