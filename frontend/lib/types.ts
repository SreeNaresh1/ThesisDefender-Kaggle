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

export interface DimensionScore {
  score: number;
  reason: string;
}

export interface ScoreBreakdown {
  evidence_quality: DimensionScore;
  assumption_strength: DimensionScore;
  counterargument_resistance: DimensionScore;
  practical_feasibility: DimensionScore;
  scope_precision: DimensionScore;
}

export interface VerdictOutput {
  resilience_score: number;
  verdict: string;
  score_explanation: string;
  score_breakdown: ScoreBreakdown;
  critical_vulnerability: string;
  recommended_revision: string;
  recommended_fixes: string[];
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
  0: "#E84B4A",   // 0-20 Collapsed
  21: "#D85A30",  // 21-40 Fragile
  41: "#BA7517",  // 41-60 Defensible
  61: "#4CAF7D",  // 61-80 Strong
  81: "#0F9E6A",  // 81-100 Robust
} as const;

export function getScoreColor(score: number): string {
  if (score <= 20) return SCORE_COLORS[0];
  if (score <= 40) return SCORE_COLORS[21];
  if (score <= 60) return SCORE_COLORS[41];
  if (score <= 80) return SCORE_COLORS[61];
  return SCORE_COLORS[81];
}

export function getScoreLabel(score: number): string {
  if (score <= 20) return "Collapsed";
  if (score <= 40) return "Fragile";
  if (score <= 60) return "Defensible";
  if (score <= 80) return "Strong";
  return "Robust";
}
