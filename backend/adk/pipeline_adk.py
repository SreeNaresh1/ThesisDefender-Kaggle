"""
ThesisDefender — ADK Pipeline Runner
======================================
Provides run_analysis_adk(), a drop-in async replacement for run_analysis()
in agents/pipeline.py when USE_ADK=True.

Architecture
------------

  run_analysis_adk()
    │
    ├── build_pipeline(model_client)   → SequentialAgent
    │     ├── OrchestratorAgent
    │     ├── DefenseCounselAgent
    │     ├── ProsecutorAgent
    │     └── JudgeAgent
    │
    ├── InMemorySessionService         → session state store
    │     └── state = {argument, job_id, queue, ...results}
    │
    ├── Runner.run_async()             → drives the SequentialAgent
    │
    └── Extract state → ArgumentAnalysis → queue.update_job(complete)

The response shape (ArgumentAnalysis) is identical to the original pipeline.
No frontend or API contract changes are required.

Session State Flow
------------------

  Initial state (set before run):
    "argument"  → str           original user argument
    "job_id"    → str           for queue progress reporting
    "queue"     → JobQueue      reference for step label updates

  Written by each agent during run:
    "structure" → ArgumentStructure   (by OrchestratorAgent)
    "defense"   → DefenseOutput       (by DefenseCounselAgent)
    "attack"    → AttackOutput        (by ProsecutorAgent)
    "verdict"   → VerdictOutput       (by JudgeAgent)
"""

import logging
import time
from datetime import datetime, timezone

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from config import settings
from models.schemas import ArgumentAnalysis
from jobs.queue import JobQueue
from adk.agents import build_pipeline
from mcp_server.client import ThesisDefenderMCPClient

logger = logging.getLogger(__name__)


async def run_analysis_adk(
    job_id: str,
    argument: str,
    model_client,
    queue: JobQueue,
) -> None:
    """
    Execute the ThesisDefender analysis pipeline via Google ADK.

    This function is a drop-in replacement for agents.pipeline.run_analysis().
    It produces an identical ArgumentAnalysis result and updates the same
    JobQueue with identical status transitions.

    Status transitions emitted:
      pending → structuring → defending → attacking → judging → complete

    Args:
        job_id:       UUID string identifying the job in the queue.
        argument:     Raw argument text submitted by the user.
        model_client: services.model_client.ModelClient instance.
        queue:        jobs.queue.JobQueue instance for progress reporting.

    On success: calls queue.update_job(status="complete", result=...)
    On failure: calls queue.update_job(status="failed", error_message=...)
    """
    start_time = time.time()

    try:
        # ---------------------------------------------------------------
        # 1. Build the ADK SequentialAgent pipeline (with MCP client)
        # ---------------------------------------------------------------
        # Create the MCP client. If the MCP server (mcp_server/run_server.py)
        # is not running, all client calls return None and enrichment is
        # skipped silently — the pipeline continues without MCP context.
        mcp_client = ThesisDefenderMCPClient(settings.MCP_SERVER_URL)

        pipeline = build_pipeline(model_client, mcp_client=mcp_client)
        logger.info(
            "[ADK Pipeline] Job %s — built SequentialAgent with %d sub-agents. MCP URL: %s",
            job_id,
            len(pipeline.sub_agents),
            settings.MCP_SERVER_URL,
        )

        # ---------------------------------------------------------------
        # 2. Set up ADK session infrastructure
        # ---------------------------------------------------------------
        session_service = InMemorySessionService()
        app_name = "thesis_defender"
        user_id  = f"job_{job_id}"

        # Seed session state:
        #   - "argument" / "job_id" / "queue" are read by agents at runtime
        #   - result keys ("structure", "defense", "attack", "verdict") are
        #     written by each agent as it completes
        initial_state = {
            "argument": argument,
            "job_id":   job_id,
            "queue":    queue,  # InMemorySessionService holds Python objects directly
        }

        session = session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state=initial_state,
        )

        # ---------------------------------------------------------------
        # 3. Create the ADK Runner and execute the pipeline
        # ---------------------------------------------------------------
        runner = Runner(
            agent=pipeline,
            app_name=app_name,
            session_service=session_service,
        )

        logger.info("[ADK Pipeline] Job %s — starting runner.", job_id)

        # run_async drives the SequentialAgent: each sub-agent runs to
        # completion before the next one starts. Queue progress updates
        # are fired inside each agent's _run_async_impl.
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=argument)]),
        ):
            # Events are handled (queue updates, logging) inside each agent.
            # We log here for observability only.
            if event.author:
                logger.debug(
                    "[ADK Runner] Job %s — event from agent: %s",
                    job_id,
                    event.author,
                )

        # ---------------------------------------------------------------
        # 4. Retrieve completed session state
        # ---------------------------------------------------------------
        final_session = session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session.id,
        )
        state = final_session.state

        # Verify all required keys are present (guards against partial runs)
        required_keys = ("structure", "defense", "attack", "verdict")
        missing = [k for k in required_keys if k not in state]
        if missing:
            raise RuntimeError(
                f"ADK pipeline completed but session state is missing keys: {missing}"
            )

        # ---------------------------------------------------------------
        # 5. Assemble ArgumentAnalysis — identical schema to original pipeline
        # ---------------------------------------------------------------
        processing_time_ms = int((time.time() - start_time) * 1000)

        analysis = ArgumentAnalysis(
            job_id=job_id,
            original_argument=argument,
            structure=state["structure"],
            defense=state["defense"],
            attack=state["attack"],
            verdict=state["verdict"],
            total_llm_calls=4,
            processing_time_ms=processing_time_ms,
            analysis_timestamp=datetime.now(timezone.utc),
        )

        # ---------------------------------------------------------------
        # 6. Mark job complete — identical to original pipeline.py behaviour
        # ---------------------------------------------------------------
        await queue.update_job(
            job_id,
            status="complete",
            result=analysis.model_dump(),
            current_step=4,
            current_step_label="Complete",
        )

        logger.info(
            "[ADK Pipeline] Job %s complete in %.1fs — score=%d.",
            job_id,
            processing_time_ms / 1000,
            state["verdict"].resilience_score,
        )

    except Exception as exc:
        logger.exception("[ADK Pipeline] Job %s failed: %s", job_id, str(exc))
        await queue.update_job(
            job_id,
            status="failed",
            error_message=str(exc),
        )
