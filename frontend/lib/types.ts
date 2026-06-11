export interface ArgumentStructure {
  main_claim: string;
  assumptions: string[];
}

export interface DefenseOutput {
  best_defense: string;
  supporting_points: string[];
}

export interface AttackOutput {
  strongest_attack: string;
  counterpoints: string[];
}

export interface VerdictOutput {
  resilience_score: number;
  verdict: string;
  critical_vulnerability: string;
  recommended_fixes: string[];
  stronger_version: string;
  reasoning_summary: string;
}

export interface ArgumentAnalysis {
  job_id: string;
  original_argument: string;
  structure: ArgumentStructure;
  defense: DefenseOutput;
  attack: AttackOutput;
  verdict: VerdictOutput;
  total_llm_calls: number;
  processing_time_ms: number;
  analysis_timestamp: string;
}

export type AnalysisStatus =
  | "pending"
  | "structuring"
  | "defending"
  | "attacking"
  | "judging"
  | "complete"
  | "failed";

export interface AnalysisJob {
  job_id: string;
  status: AnalysisStatus;
  current_step: number;
  current_step_label: string;
  result: ArgumentAnalysis | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export const SCORE_COLORS = {
  0: "#E84B4A",   // 0-15 Fragile
  16: "#D85A30",  // 16-30 Weak
  31: "#BA7517",  // 31-50 Mixed
  51: "#4CAF7D",  // 51-70 Defensible
  71: "#1DB87A",  // 71-85 Resilient
  86: "#0F9E6A",  // 86-100 Bulletproof
} as const;

export function getScoreColor(score: number): string {
  if (score <= 15) return SCORE_COLORS[0];
  if (score <= 30) return SCORE_COLORS[16];
  if (score <= 50) return SCORE_COLORS[31];
  if (score <= 70) return SCORE_COLORS[51];
  if (score <= 85) return SCORE_COLORS[71];
  return SCORE_COLORS[86];
}

export function getScoreLabel(score: number): string {
  if (score <= 15) return "Fragile";
  if (score <= 30) return "Weak";
  if (score <= 50) return "Mixed";
  if (score <= 70) return "Defensible";
  if (score <= 85) return "Resilient";
  return "Bulletproof";
}
