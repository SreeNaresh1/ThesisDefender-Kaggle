"""
ThesisDefender — Google ADK Agent Definitions
===============================================
Defines four BaseAgent subclasses that each wrap one step of the existing
LLM pipeline. Each agent reuses the original system prompts, scoring rubric,
and response schemas from agents/pipeline.py and models/schemas.py without
modification.

Agent execution order (declared via SequentialAgent in build_pipeline()):

  OrchestratorAgent   — Call 1: extract main_claim + assumptions
         ↓
  DefenseCounselAgent — Call 2a: steel-man the argument
         ↓
  ProsecutorAgent     — Call 2b: attack the steel-manned defense
         ↓
  JudgeAgent          — Call 3: assign resilience score + verdict

Inter-agent state is shared via InvocationContext.session.state, a plain
Python dict that persists across all agents in the same session.

State keys
----------
  STATE_ARGUMENT   : str               — original user argument
  STATE_JOB_ID     : str               — job id for queue progress updates
  STATE_QUEUE      : JobQueue          — queue reference for step reporting
  STATE_STRUCTURE  : ArgumentStructure — output of OrchestratorAgent
  STATE_DEFENSE    : DefenseOutput     — output of DefenseCounselAgent
  STATE_ATTACK     : AttackOutput      — output of ProsecutorAgent
  STATE_VERDICT    : VerdictOutput     — output of JudgeAgent
"""

import logging
from typing import Any, AsyncGenerator

from pydantic import ConfigDict

from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from models.schemas import ArgumentStructure, DefenseOutput, AttackOutput, VerdictOutput
from agents.pipeline import (
    _robust_llm_call,
    SYSTEM_PROMPT_ORCHESTRATOR,
    SYSTEM_PROMPT_DEFENSE,
    SYSTEM_PROMPT_PROSECUTOR,
    SYSTEM_PROMPT_JUDGE,
)
from helpers.formatting import (
    build_defense_user_prompt,
    build_prosecutor_user_prompt,
    build_judge_user_prompt,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session state key constants — shared across all agents
# ---------------------------------------------------------------------------
STATE_ARGUMENT = "argument"
STATE_JOB_ID   = "job_id"
STATE_QUEUE    = "queue"
STATE_STRUCTURE = "structure"
STATE_DEFENSE   = "defense"
STATE_ATTACK    = "attack"
STATE_VERDICT   = "verdict"
# Written by OrchestratorAgent after an MCP verify_claim_type call;
# read by ProsecutorAgent to inject targeted attack vectors into its prompt.
STATE_MCP_ENRICHMENT = "mcp_enrichment"


# ---------------------------------------------------------------------------
# Agent 1 — Orchestrator
# ---------------------------------------------------------------------------

class OrchestratorAgent(BaseAgent):
    """
    Parse the argument. Extract the main_claim and all implicit assumptions.

    Reuses: SYSTEM_PROMPT_ORCHESTRATOR (from agents/pipeline.py)
    Schema:  ArgumentStructure (from models/schemas.py)
    LLM params: temperature=0.1, max_tokens=2000
    Writes: state[STATE_STRUCTURE]

    MCP integration (Phase 2):
    After extracting the structure, optionally calls the MCP server tool
    verify_claim_type(main_claim) to identify the logical claim type and
    pre-load targeted attack vectors into state[STATE_MCP_ENRICHMENT].
    ProsecutorAgent reads this enrichment and injects the attack vectors
    into its prompt, resulting in more precise, claim-type-aware attacks.
    If the MCP server is offline, mcp_client returns None and enrichment
    is skipped — the pipeline continues unchanged.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_client: Any
    mcp_client: Any = None  # Optional[ThesisDefenderMCPClient]; None = no MCP enrichment

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        argument = ctx.session.state[STATE_ARGUMENT]
        queue    = ctx.session.state.get(STATE_QUEUE)
        job_id   = ctx.session.state.get(STATE_JOB_ID)

        # Report step start to the job queue (mirrors original pipeline.py)
        if queue and job_id:
            await queue.update_job(
                job_id,
                status="structuring",
                current_step=1,
                current_step_label="Orchestrator: Extracting claim and assumptions...",
            )

        structure: ArgumentStructure = await _robust_llm_call(
            self.model_client,
            SYSTEM_PROMPT_ORCHESTRATOR,
            f"Argument to analyze:\n\n{argument}",
            temperature=0.1,
            max_tokens=1000,
            schema_class=ArgumentStructure,
        )

        ctx.session.state[STATE_STRUCTURE] = structure
        logger.info(
            "[OrchestratorAgent] Claim extracted: %r (category=%s)",
            structure.main_claim,
            getattr(structure, "category", "—"),
        )

        # -------------------------------------------------------------------
        # MCP Tool Call: verify_claim_type
        # Identifies the logical type of the extracted claim and pre-loads
        # targeted attack vectors into session state for ProsecutorAgent.
        # Fails silently if the MCP server is not running.
        # -------------------------------------------------------------------
        if self.mcp_client is not None:
            logger.info(
                "[OrchestratorAgent] Calling MCP tool: verify_claim_type(%r)",
                structure.main_claim[:80],
            )
            enrichment = await self.mcp_client.verify_claim_type(structure.main_claim)
            if enrichment:
                ctx.session.state[STATE_MCP_ENRICHMENT] = enrichment
                logger.info(
                    "[OrchestratorAgent] MCP enrichment stored: claim_type=%r, confidence=%.2f",
                    enrichment.get("claim_type"),
                    enrichment.get("confidence", 0.0),
                )
            else:
                logger.debug("[OrchestratorAgent] MCP server returned no enrichment (offline?).")

        yield Event(author=self.name, invocation_id=ctx.invocation_id, custom_metadata={"state": ctx.session.state})


# ---------------------------------------------------------------------------
# Agent 2 — Defense Counsel
# ---------------------------------------------------------------------------

class DefenseCounselAgent(BaseAgent):
    """
    Build the strongest possible (steel-manned) version of the argument.

    Reuses: SYSTEM_PROMPT_DEFENSE, build_defense_user_prompt()
    Schema:  DefenseOutput
    LLM params: temperature=0.3, max_tokens=3000
    Reads:  state[STATE_STRUCTURE]
    Writes: state[STATE_DEFENSE]
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_client: Any

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        argument  = ctx.session.state[STATE_ARGUMENT]
        structure = ctx.session.state[STATE_STRUCTURE]
        queue     = ctx.session.state.get(STATE_QUEUE)
        job_id    = ctx.session.state.get(STATE_JOB_ID)

        if queue and job_id:
            await queue.update_job(
                job_id,
                status="defending",
                current_step=2,
                current_step_label="Defense Counsel: Building the strongest case...",
            )

        defense: DefenseOutput = await _robust_llm_call(
            self.model_client,
            SYSTEM_PROMPT_DEFENSE,
            build_defense_user_prompt(argument, structure),
            temperature=0.3,
            max_tokens=1000,
            schema_class=DefenseOutput,
        )

        ctx.session.state[STATE_DEFENSE] = defense
        logger.info(
            "[DefenseCounselAgent] Defense built (%d supporting points).",
            len(defense.supporting_points),
        )

        yield Event(author=self.name, invocation_id=ctx.invocation_id, custom_metadata={"state": ctx.session.state})


# ---------------------------------------------------------------------------
# Agent 3 — Prosecutor
# ---------------------------------------------------------------------------

class ProsecutorAgent(BaseAgent):
    """
    Construct the most devastating attack against the steel-manned defense.

    Reuses: SYSTEM_PROMPT_PROSECUTOR, build_prosecutor_user_prompt()
    Schema:  AttackOutput
    LLM params: temperature=0.3, max_tokens=3000
    Reads:  state[STATE_STRUCTURE], state[STATE_DEFENSE]
    Writes: state[STATE_ATTACK]

    MCP integration (Phase 2):
    If state[STATE_MCP_ENRICHMENT] was populated by OrchestratorAgent,
    injects the MCP-sourced typical_attack_vectors as a context block
    appended to the existing build_prosecutor_user_prompt() output.
    The base prompt function is NOT modified — enrichment is purely additive.
    If MCP enrichment is absent, the prompt is identical to the original.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_client: Any

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        argument  = ctx.session.state[STATE_ARGUMENT]
        structure = ctx.session.state[STATE_STRUCTURE]
        defense   = ctx.session.state[STATE_DEFENSE]
        queue     = ctx.session.state.get(STATE_QUEUE)
        job_id    = ctx.session.state.get(STATE_JOB_ID)

        if queue and job_id:
            await queue.update_job(
                job_id,
                status="attacking",
                current_step=3,
                current_step_label="Prosecutor: Finding critical flaws...",
            )

        # Build base prompt (unchanged function from helpers/formatting.py)
        prosecutor_prompt = build_prosecutor_user_prompt(argument, structure, defense)

        # -------------------------------------------------------------------
        # MCP Enrichment Injection
        # If OrchestratorAgent stored MCP-sourced attack vectors, append
        # them as a context block. The LLM is free to use or ignore them.
        # build_prosecutor_user_prompt() itself is NOT modified.
        # -------------------------------------------------------------------
        enrichment = ctx.session.state.get(STATE_MCP_ENRICHMENT)
        if enrichment and enrichment.get("typical_attack_vectors"):
            claim_type   = enrichment.get("claim_type", "unknown")
            attack_lines = "\n".join(
                f"  • {v}" for v in enrichment["typical_attack_vectors"]
            )
            scrutiny_lines = ""
            if enrichment.get("scrutiny_questions"):
                scrutiny_lines = "\n" + "\n".join(
                    f"  • {q}" for q in enrichment["scrutiny_questions"]
                )
            prosecutor_prompt += (
                f"\n\n[MCP CONTEXT — Claim Type: {claim_type.upper()}]\n"
                f"Suggested attack angles identified by MCP verify_claim_type tool:\n"
                f"{attack_lines}"
                f"{scrutiny_lines}"
            )
            logger.info(
                "[ProsecutorAgent] MCP enrichment injected: %d attack vectors for claim_type=%r.",
                len(enrichment["typical_attack_vectors"]),
                claim_type,
            )

        attack: AttackOutput = await _robust_llm_call(
            self.model_client,
            SYSTEM_PROMPT_PROSECUTOR,
            prosecutor_prompt,
            temperature=0.3,
            max_tokens=1000,
            schema_class=AttackOutput,
        )

        ctx.session.state[STATE_ATTACK] = attack
        logger.info(
            "[ProsecutorAgent] Attack constructed (%d counterpoints).",
            len(attack.counterpoints),
        )

        yield Event(author=self.name, invocation_id=ctx.invocation_id, custom_metadata={"state": ctx.session.state})


# ---------------------------------------------------------------------------
# Agent 4 — Judge
# ---------------------------------------------------------------------------

class JudgeAgent(BaseAgent):
    """
    Evaluate the full case. Assign Resilience Score (0-100) and verdict.

    Reuses: SYSTEM_PROMPT_JUDGE (full scoring rubric), build_judge_user_prompt()
    Schema:  VerdictOutput
    LLM params: temperature=0.0, max_tokens=4000  (deterministic)
    Reads:  state[STATE_STRUCTURE], state[STATE_DEFENSE], state[STATE_ATTACK]
    Writes: state[STATE_VERDICT]
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_client: Any

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        argument  = ctx.session.state[STATE_ARGUMENT]
        structure = ctx.session.state[STATE_STRUCTURE]
        defense   = ctx.session.state[STATE_DEFENSE]
        attack    = ctx.session.state[STATE_ATTACK]
        queue     = ctx.session.state.get(STATE_QUEUE)
        job_id    = ctx.session.state.get(STATE_JOB_ID)

        if queue and job_id:
            await queue.update_job(
                job_id,
                status="judging",
                current_step=4,
                current_step_label="Judge: Assigning verdict and score...",
            )

        verdict: VerdictOutput = await _robust_llm_call(
            self.model_client,
            SYSTEM_PROMPT_JUDGE,
            build_judge_user_prompt(argument, structure, defense, attack),
            temperature=0.0,
            max_tokens=1000,
            schema_class=VerdictOutput,
        )

        ctx.session.state[STATE_VERDICT] = verdict
        logger.info(
            "[JudgeAgent] Verdict: resilience_score=%d, label=%r",
            verdict.resilience_score,
            verdict.verdict,
        )

        yield Event(
            author=self.name, 
            invocation_id=ctx.invocation_id,
            custom_metadata={"state": ctx.session.state}
        )


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def build_pipeline(model_client: Any, mcp_client: Any = None) -> SequentialAgent:
    """
    Construct and return the ThesisDefender ADK SequentialAgent.

    The pipeline executes agents in strict sequential order:
      orchestrator → defense_counsel → prosecutor → judge

    Each agent receives the same InvocationContext and communicates
    via ctx.session.state.

    Args:
        model_client: An instance of services.model_client.ModelClient.
        mcp_client:   Optional ThesisDefenderMCPClient. When provided, the
                      OrchestratorAgent calls verify_claim_type() after
                      structure extraction, and ProsecutorAgent receives
                      MCP-sourced attack vectors in its prompt.
                      Pass None (default) to disable MCP enrichment.

    Returns:
        A configured SequentialAgent ready to be passed to an ADK Runner.

    Example:
        # Without MCP (USE_ADK=True, MCP server not running):
        pipeline = build_pipeline(model_client)

        # With MCP enrichment (MCP server running on port 8001):
        from mcp_server.client import ThesisDefenderMCPClient
        mcp = ThesisDefenderMCPClient(settings.MCP_SERVER_URL)
        pipeline = build_pipeline(model_client, mcp_client=mcp)

        runner = Runner(agent=pipeline, app_name="thesis_defender",
                        session_service=InMemorySessionService())
    """
    return SequentialAgent(
        name="thesis_defender_pipeline",
        description=(
            "Adversarial multi-agent argument analysis: "
            "Orchestrator → Defense Counsel → Prosecutor → Judge"
        ),
        sub_agents=[
            OrchestratorAgent(
                name="orchestrator",
                description="Extracts main claim and implicit assumptions; calls MCP verify_claim_type",
                model_client=model_client,
                mcp_client=mcp_client,  # None = MCP enrichment disabled
            ),
            DefenseCounselAgent(
                name="defense_counsel",
                description="Steel-mans the argument into its strongest form",
                model_client=model_client,
            ),
            ProsecutorAgent(
                name="prosecutor",
                description="Constructs the most devastating counterargument, enriched by MCP attack vectors",
                model_client=model_client,
            ),
            JudgeAgent(
                name="judge",
                description="Evaluates and assigns Resilience Score 0-100",
                model_client=model_client,
            ),
        ],
    )
