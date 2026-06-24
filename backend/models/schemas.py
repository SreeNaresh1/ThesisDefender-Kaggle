from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class ArgumentStructure(BaseModel):
    main_claim: str
    assumptions: list[str]

class DefenseOutput(BaseModel):
    best_defense: str
    supporting_points: list[str]

class AttackOutput(BaseModel):
    strongest_attack: str
    counterpoints: list[str]

class DimensionScore(BaseModel):
    score: int = Field(ge=0, le=20)
    reason: str

class ScoreBreakdown(BaseModel):
    evidence_quality: DimensionScore
    assumption_strength: DimensionScore
    counterargument_resistance: DimensionScore
    practical_feasibility: DimensionScore
    scope_precision: DimensionScore

class VerdictOutput(BaseModel):
    resilience_score: int = Field(ge=0, le=100)
    verdict: str
    score_explanation: str
    score_breakdown: ScoreBreakdown
    critical_vulnerability: str
    recommended_revision: str
    recommended_fixes: list[str]

class ArgumentAnalysis(BaseModel):
    job_id: str
    original_argument: str
    structure: ArgumentStructure
    defense: DefenseOutput
    attack: AttackOutput
    verdict: VerdictOutput
    total_llm_calls: int
    processing_time_ms: int
    analysis_timestamp: datetime

class AnalysisJob(BaseModel):
    job_id: str
    status: Literal["pending", "structuring", "defending", "attacking", "judging", "complete", "failed"]
    current_step: int
    current_step_label: str
    result: Optional[ArgumentAnalysis] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AnalysisRequest(BaseModel):
    argument: str = Field(min_length=2, max_length=3000)

def get_score_label(score: int) -> str:
    if score <= 20:
        return "Collapsed"
    elif score <= 40:
        return "Fragile"
    elif score <= 60:
        return "Defensible"
    elif score <= 80:
        return "Strong"
    else:
        return "Robust"

def get_score_color(score: int) -> str:
    if score <= 20:
        return "#E84B4A" # Red
    elif score <= 40:
        return "#D85A30" # Orange-Red
    elif score <= 60:
        return "#BA7517" # Amber
    elif score <= 80:
        return "#4CAF7D" # Light Green
    else:
        return "#0F9E6A" # Deep Green
