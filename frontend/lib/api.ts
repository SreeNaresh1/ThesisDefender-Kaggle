import { AnalysisJob, ArgumentAnalysis } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function startAnalysis(argument: string): Promise<{ job_id: string }> {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ argument }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(data?.detail || "Failed to start analysis", res.status);
  }
  return res.json();
}

export async function getJobStatus(job_id: string): Promise<AnalysisJob> {
  const res = await fetch(`${BASE}/api/analyze/status/${job_id}`);
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(data?.detail || "Failed to fetch job status", res.status);
  }
  return res.json();
}

export async function getResult(job_id: string): Promise<ArgumentAnalysis> {
  const res = await fetch(`${BASE}/api/analyze/result/${job_id}`);
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(data?.detail || "Failed to fetch result", res.status);
  }
  return res.json();
}
