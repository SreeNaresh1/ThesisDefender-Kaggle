"""
ThesisDefender CLI — Local Queue Adapter
==========================================
Provides CliQueue: a drop-in replacement for jobs.queue.JobQueue that works
without Redis and without a running FastAPI server.

The existing run_analysis() function requires a JobQueue object for two things:
  1. create_job()   — initialise the job record
  2. update_job()   — emit step-label progress and store the final result

CliQueue satisfies both while adding live progress printing to the terminal.
The final ArgumentAnalysis result is captured in self.result after the pipeline
runs, ready for the CLI to format and save.

No pipeline logic is duplicated. No new LLM calls are made. The CLI workflow is:

  CliQueue()
    ↓
  run_analysis(job_id, argument, model_client, foundry_client=None, queue=cli_queue)
    ↓ (internally calls Orchestrator → Defense → Prosecutor → Judge, or ADK path)
  cli_queue.result  →  ArgumentAnalysis
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from models.schemas import AnalysisJob, ArgumentAnalysis

logger = logging.getLogger(__name__)


class CliQueue:
    """
    In-process JobQueue adapter for the CLI.

    Satisfies the interface expected by run_analysis() and run_analysis_adk():
      - create_job(job)             — store initial job record
      - update_job(job_id, **kw)   — update status; print progress; capture result
      - get_job(job_id)             — retrieve current job record
      - connect() / close()         — no-ops (no Redis needed)

    After run_analysis() completes, inspect:
      - self.result   : Optional[ArgumentAnalysis]   — None if job failed
      - self.error    : Optional[str]                — error message if failed
      - self.steps    : list[str]                    — ordered step labels emitted
    """

    STEP_ICONS = {
        "pending":     "⏳",
        "structuring": "🔍",
        "defending":   "🛡️ ",
        "attacking":   "⚔️ ",
        "judging":     "⚖️ ",
        "complete":    "✅",
        "failed":      "❌",
    }

    def __init__(self, show_progress: bool = True):
        """
        Args:
            show_progress: If True, print step labels to stdout as they arrive.
                           Set False in tests to suppress output.
        """
        self._store: dict[str, AnalysisJob] = {}
        self.result: Optional[ArgumentAnalysis] = None
        self.error:  Optional[str]             = None
        self.steps:  list[str]                 = []
        self.show_progress = show_progress

    # ------------------------------------------------------------------
    # JobQueue interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """No-op: CLI uses in-process storage."""

    async def close(self) -> None:
        """No-op."""

    async def create_job(self, job: AnalysisJob) -> str:
        self._store[job.job_id] = job
        return job.job_id

    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        return self._store.get(job_id)

    async def update_job(self, job_id: str, **kwargs) -> None:
        job = self._store.get(job_id)
        if not job:
            return

        job_dict = job.model_dump()
        for k, v in kwargs.items():
            job_dict[k] = v
        job_dict["updated_at"] = datetime.now(timezone.utc)

        updated = AnalysisJob.model_validate(job_dict)
        self._store[job_id] = updated

        # Capture result / error
        if updated.status == "complete" and updated.result:
            self.result = ArgumentAnalysis.model_validate(updated.result)
        elif updated.status == "failed":
            self.error = updated.error_message or "Unknown error"

        # Progress reporting
        label = kwargs.get("current_step_label", updated.current_step_label)
        status = kwargs.get("status", updated.status)
        if label and label not in self.steps:
            self.steps.append(label)

        if self.show_progress:
            icon = self.STEP_ICONS.get(status, "•")
            step_num = kwargs.get("current_step", updated.current_step)
            if status not in ("complete", "failed"):
                print(f"  {icon} Step {step_num}/4  {label}", flush=True)
            elif status == "complete":
                print(f"  {icon} Analysis complete.", flush=True)
            elif status == "failed":
                print(f"  {icon} Analysis failed: {self.error}", flush=True)
