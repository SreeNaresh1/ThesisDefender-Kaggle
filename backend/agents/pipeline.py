import logging
import time
import json
import pydantic
from datetime import datetime, timezone

from config import settings
from models.schemas import ArgumentAnalysis, ArgumentStructure, DefenseOutput, AttackOutput, VerdictOutput
from services.model_client import ModelClient
from jobs.queue import JobQueue
from helpers.formatting import build_defense_user_prompt, build_prosecutor_user_prompt, build_judge_user_prompt

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_ORCHESTRATOR = """You are the Orchestrator Agent. Your job is to parse the user's input, extract the main claim, and explicitly list the underlying assumptions required for the claim to be true.

Return ONLY valid JSON matching this schema:
{
  "main_claim": "The single central assertion in one clear sentence",
  "assumptions": ["Unstated premise 1", "Unstated premise 2"],
  "category": "Science | Technology | Business | Politics | Ethics | Health | Education | Environment | Other",
  "claim_type": "factual | predictive | ethical | policy | subjective | causal"
}"""

SYSTEM_PROMPT_DEFENSE = """You are the Defense Counsel Agent. Your job is to construct the strongest possible version of the original argument (a steel-man). 
Fill in logical gaps charitably and add supporting logic. Do not strawman the argument.

Target 60-120 words per section. Be concise. Avoid repetition.

Return ONLY valid JSON matching this schema:
{
  "best_defense": "A robust paragraph presenting the absolute strongest version of the argument",
  "supporting_points": ["Strong supporting logic 1", "Strong supporting logic 2", "Strong supporting logic 3"]
}"""

SYSTEM_PROMPT_PROSECUTOR = """You are the Prosecutor Agent. Your job is to read the Defense Counsel's steel-manned version of the argument, and construct the most devastating attack against it.
Find logical gaps, hidden assumptions, counterexamples, and attack the strongest version of their claim.

Important: Provide 3 distinct, varied angles of attack. Do not repeat the same idea. Attack from different vectors such as causality, data quality, geographic variation, or historical exceptions.
Do not invent flaws where none exist. If the claim is strongly supported, focus on limitations, scope conditions, or edge cases.

Target 60-120 words per section. Be concise. Avoid repetition.

Return ONLY valid JSON matching this schema:
{
  "strongest_attack": "A powerful counterargument specifically targeting the defense's steel-man",
  "counterpoints": ["Specific flaw 1", "Specific flaw 2", "Specific flaw 3"]
}"""

SYSTEM_PROMPT_JUDGE = """You are the Judge Agent. You have seen the original argument, the Defense Counsel's steel-man, and the Prosecutor's attack.
Evaluate the overall quality of the original argument.

Target 60-120 words per section. Be concise. Avoid repetition.

Avoid score compression. Use the full 0-100 scale.
Arguments that are scientifically established, universally accepted, or supported by overwhelming evidence should score above 90.
Arguments that are demonstrably false or collapse under scrutiny should score below 20.
Do not default to middle-range scores.

Scoring Rubric (0-100):
0-20 = Fragile (core claim collapses)
21-40 = Weak (major flaws significantly undermine claim)
41-60 = Defensible (core claim survives but important weaknesses remain)
61-80 = Strong (core claim largely withstands attack)
81-100 = Robust (attack fails to substantially weaken claim)

Confidence Score Guidelines:
90-100: Strong evidence and little ambiguity.
70-89: Generally reliable evaluation with some uncertainty.
50-69: Meaningful uncertainty due to assumptions or limited evidence.
0-49: Highly speculative or subjective claim where confidence is low.

Important Guidelines:
- Do not over-penalize nuanced or highly qualified statements. Acknowledging complexity (e.g. 'sanitation also helped reduce disease') should be treated as a strength, not a fatal flaw. 
- Only dock significant points if the core claim is fully undermined by the attack. Score charitably when the argument is generally sound despite minor confounders.
- An argument should receive a score of 70+ if the Prosecutor's strongest attack primarily identifies nuance, exceptions, confounders, or scope limitations rather than disproving the core claim.
- Undisputable scientific facts, universally accepted empirical truths, or statements that cannot be meaningfully attacked must receive a Robust score (90-100).
- If the attack only narrows scope or adds nuance, the score should remain Strong (61-80) or Robust (81-100).

Consistency Requirements:
- If resilience_score >= 81, the verdict should describe the argument as Robust.
- If resilience_score is between 61 and 80, the verdict should describe it as Strong.
- If resilience_score is between 41 and 60, the verdict should describe it as Defensible.
- If resilience_score is between 21 and 40, the verdict should describe it as Weak.
- If resilience_score is 20 or below, the verdict should describe it as Fragile.
- The reasoning_summary must clearly justify the assigned score.
- The critical_vulnerability must identify the single most damaging weakness. If no major weakness exists, state the strongest limitation rather than inventing a flaw.
- The stronger_version should preserve the original intent while eliminating unsupported certainty, overgeneralization, or ambiguous wording.

Return ONLY valid JSON matching this schema. CRITICAL: You MUST independently calculate the `resilience_score` and `confidence` (0-100). Do not just copy the placeholder value of 0:
{
  "resilience_score": 0,
  "confidence": 0,
  "verdict": "Short verdict summarizing the evaluation",
  "argument_strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "critical_vulnerability": "The single weakest premise or unsupported leap that breaks the argument",
  "recommended_fixes": ["Actionable fix 1", "Actionable fix 2", "Actionable fix 3"],
  "stronger_version": "A rewritten, highly defensible version of the original claim",
  "reasoning_summary": "A brief summary of how the score was decided based on the defense vs attack"
}"""

from security.guards import validate_llm_output, OutputValidationError

async def _robust_llm_call(model_client: ModelClient, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int, schema_class):
    for attempt in range(3):
        try:
            data = await model_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if not data:
                raise ValueError("Empty response received")
            result = schema_class.model_validate(data)
            # Layer 4 — business-rule validation beyond Pydantic schema
            validate_llm_output(result)
            return result
        except (json.JSONDecodeError, pydantic.ValidationError, ValueError, OutputValidationError) as e:
            if attempt == 2:
                raise e
            logger.warning(f"LLM call failed (attempt {attempt+1}), retrying: {e}")
            system_prompt += f"\n\nCRITICAL: Previous response failed validation: {str(e)}. Return ONLY valid JSON matching the schema."

async def run_analysis(
    job_id: str,
    argument: str,
    model_client: ModelClient,
    foundry_client,  # Ignored, kept for signature compatibility
    queue: JobQueue
) -> None:
    # -----------------------------------------------------------------------
    # ADK dispatch — opt-in via USE_ADK=true in environment / .env
    # When enabled, delegates to the ADK SequentialAgent pipeline.
    # When disabled (default), runs the original 4-call logic below.
    # The import is lazy so that google-adk is not required when USE_ADK=False.
    # -----------------------------------------------------------------------
    if settings.USE_ADK:
        logger.info("[pipeline] USE_ADK=True — delegating to ADK runner for job %s", job_id)
        from adk.pipeline_adk import run_analysis_adk  # lazy import
        await run_analysis_adk(
            job_id=job_id,
            argument=argument,
            model_client=model_client,
            queue=queue,
        )
        return

    # -----------------------------------------------------------------------
    # Original pipeline (USE_ADK=False, default)
    # 4 sequential LLM calls: Orchestrator → Defense → Prosecutor → Judge
    # -----------------------------------------------------------------------
    start_time = time.time()
    try:
        # Step 1: Orchestrator
        await queue.update_job(
            job_id,
            status="structuring",
            current_step=1,
            current_step_label="Orchestrator: Extracting claim and assumptions..."
        )
        
        structure = await _robust_llm_call(
            model_client,
            SYSTEM_PROMPT_ORCHESTRATOR,
            f"Argument to analyze:\n\n{argument}",
            0.1,
            2000,
            ArgumentStructure
        )

        # Step 2: Defense Counsel
        await queue.update_job(
            job_id,
            status="defending",
            current_step=2,
            current_step_label="Defense Counsel: Building the strongest case..."
        )
        
        defense = await _robust_llm_call(
            model_client,
            SYSTEM_PROMPT_DEFENSE,
            build_defense_user_prompt(argument, structure),
            0.3,
            3000,
            DefenseOutput
        )

        # Step 3: Prosecutor
        await queue.update_job(
            job_id,
            status="attacking",
            current_step=3,
            current_step_label="Prosecutor: Finding critical flaws..."
        )
        
        attack = await _robust_llm_call(
            model_client,
            SYSTEM_PROMPT_PROSECUTOR,
            build_prosecutor_user_prompt(argument, structure, defense),
            0.3,
            3000,
            AttackOutput
        )

        # Step 4: Judge
        await queue.update_job(
            job_id,
            status="judging",
            current_step=4,
            current_step_label="Judge: Assigning verdict and score..."
        )
        
        verdict = await _robust_llm_call(
            model_client,
            SYSTEM_PROMPT_JUDGE,
            build_judge_user_prompt(argument, structure, defense, attack),
            0.0,
            4000,
            VerdictOutput
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        analysis = ArgumentAnalysis(
            job_id=job_id,
            original_argument=argument,
            structure=structure,
            defense=defense,
            attack=attack,
            verdict=verdict,
            total_llm_calls=4,
            processing_time_ms=processing_time_ms,
            analysis_timestamp=datetime.now(timezone.utc)
        )
        
        await queue.update_job(
            job_id,
            status="complete",
            result=analysis.model_dump(),
            current_step=4,
            current_step_label="Complete"
        )

    except Exception as e:
        logger.exception(f"Analysis job {job_id} failed: {str(e)}")
        await queue.update_job(
            job_id,
            status="failed",
            error_message=str(e)
        )
