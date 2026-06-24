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

SYSTEM_PROMPT_JUDGE = """You are the Judge Agent in ThesisDefender.

Your responsibility is not to determine whether a claim is true.

Your responsibility is to evaluate how resilient the argument remains after being challenged by the strongest available counterarguments.

You will receive:

1. Original Claim
2. Steel-Man Defense
3. Strongest Attack

Your task is to score argument resilience using the rubric below.

SCORING FRAMEWORK

Evaluate the argument across five independent dimensions.

1. Evidence Quality (0-20)
   Measures whether the defense provides concrete evidence, examples, mechanisms, or reasoning.

0-5:
Pure assertion with little support.

6-10:
Some supporting logic but weak evidence.

11-15:
Reasonably supported with examples or mechanisms.

16-20:
Strongly supported with compelling evidence and reasoning.

2. Assumption Strength (0-20)
   Measures how dependent the argument is on unproven assumptions.

0-5:
Relies heavily on speculative assumptions.

6-10:
Several important assumptions remain unproven.

11-15:
Most assumptions are plausible and defensible.

16-20:
Assumptions are explicit, realistic, and well-supported.

3. Counterargument Resistance (0-20)
   Measures how well the defense survives the strongest attack.

0-5:
Attack severely undermines the claim.

6-10:
Attack exposes major weaknesses.

11-15:
Attack weakens but does not destroy the argument.

16-20:
Argument remains largely intact despite criticism.

4. Practical Feasibility (0-20)
   Measures real-world plausibility and implementation feasibility.

0-5:
Highly unrealistic.

6-10:
Faces major practical obstacles.

11-15:
Reasonably achievable.

16-20:
Highly plausible in real-world conditions.

5. Scope Precision (0-20)
   Measures whether the claim avoids overgeneralization.

0-5:
Extremely broad or exaggerated.

6-10:
Noticeable overgeneralization.

11-15:
Mostly well-scoped.

16-20:
Carefully framed with minimal overreach.

TOTAL SCORE

Total Score =
Evidence Quality +
Assumption Strength +
Counterargument Resistance +
Practical Feasibility +
Scope Precision

Maximum = 100

VERDICT RULES

0-20:
Collapsed

21-40:
Fragile

41-60:
Defensible

61-80:
Strong

81-100:
Robust

OUTPUT FORMAT

Return valid JSON only.

{
"resilience_score": 45,
"verdict": "Defensible",
"score_explanation": "A brief summary of how the score was decided.",
"score_breakdown": {
"evidence_quality": {
"score": 12,
"reason": "Provides supporting logic but lacks concrete evidence."
},
"assumption_strength": {
"score": 8,
"reason": "Depends heavily on future AI capability assumptions."
},
"counterargument_resistance": {
"score": 10,
"reason": "Counterarguments expose major weaknesses but do not fully invalidate the claim."
},
"practical_feasibility": {
"score": 7,
"reason": "Significant economic and technical barriers remain."
},
"scope_precision": {
"score": 8,
"reason": "Claim overgeneralizes software development work."
}
},
"critical_vulnerability": "The argument equates coding automation with replacement of the entire software development profession.",
"recommended_revision": "Narrow the claim to routine coding tasks rather than full developer replacement.",
"recommended_fixes": ["Fix 1", "Fix 2"]
}

IMPORTANT SCORING RULES

CRITICAL MATHEMATICAL REQUIREMENT:
The `resilience_score` MUST EXACTLY EQUAL the sum of the 5 scores inside `score_breakdown`. Double check your math before returning the JSON!

CROSS-CHECK CATEGORY CONSISTENCY:
If Counterargument Resistance is low, Assumption Strength and Evidence Quality should not remain extremely high unless clearly justified in your reasons. Explain any major score differences between dimensions to reduce random scoring.

Do not anchor scores around a fixed range.

Different claims should naturally receive different scores.

Examples:

Flat Earth claim:
0-15

Poorly supported speculative claim:
15-35

Interesting but flawed claim:
35-55

Reasonably defensible claim:
55-75

Strongly supported claim:
75-90

Exceptionally resilient claim:
90-100

A score of 50 should not be considered the default.

Only assign high scores when the defense remains persuasive after considering the strongest attack.

Only assign low scores when the attack fundamentally damages the argument.

Score based on resilience, not personal agreement with the claim.
"""

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
            1000,
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
            1000,
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
            1000,
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
            1000,
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
