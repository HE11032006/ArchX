"use client";

import { useCallback, useEffect, useState } from "react";

import { getJob } from "@/features/scan/api/analyze";
import type { JobResponse } from "@/shared/types/job";

const POLL_INTERVAL_MS = 1000;

export function useScanJob(jobId: string) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const poll = useCallback(async () => {
    try {
      const data = await getJob(jobId);
      setJob(data);
      setError(data.status === "failed" ? (data.error ?? "Analysis failed") : null);
      setLoading(false);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch job status";
      setError(message);
      setLoading(false);
      return null;
    }
  }, [jobId]);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    const run = async () => {
      const data = await poll();
      if (!active || !data) return;
      if (data.status !== "completed" && data.status !== "failed") {
        timer = setTimeout(run, POLL_INTERVAL_MS);
      }
    };

    run();

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [poll]);

  return { job, error, loading };
}
