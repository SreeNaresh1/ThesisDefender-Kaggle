import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
import json

from models.schemas import AnalysisJob, ArgumentAnalysis
from agents.pipeline import run_analysis
from jobs.queue import JobQueue

@pytest.fixture
def mock_model_client():
    client = AsyncMock()
    # Setup mock returns based on the call index to simulate the 4 steps
    return client

@pytest.fixture
def mock_queue():
    return AsyncMock(spec=JobQueue)

@pytest.mark.asyncio
async def test_4_agent_pipeline_execution(mock_model_client, mock_queue):
    mock_model_client.complete_json.side_effect = [
        # Orchestrator
        {
            "main_claim": "AI will replace jobs",
            "assumptions": ["assumption 1", "assumption 2"]
        },
        {
            "best_defense": "This is the best defense text, which is longer than twenty characters.",
            "supporting_points": ["point 1", "point 2"]
        },
        {
            "strongest_attack": "This is the strongest attack text, which is also longer than twenty chars.",
            "counterpoints": ["counter 1", "counter 2"]
        },
        # Judge
        {
            "resilience_score": 68,
            "verdict": "Strong results",
            "score_explanation": "Summary of reasoning.",
            "score_breakdown": {
                "evidence_quality": {"score": 14, "reason": "reason"},
                "assumption_strength": {"score": 14, "reason": "reason"},
                "counterargument_resistance": {"score": 14, "reason": "reason"},
                "practical_feasibility": {"score": 13, "reason": "reason"},
                "scope_precision": {"score": 13, "reason": "reason"}
            },
            "critical_vulnerability": "The main vulnerability.",
            "recommended_revision": "A much better claim.",
            "recommended_fixes": ["fix 1", "fix 2", "fix 3"]
        }
    ]

    await run_analysis("job123", "Some argument", mock_model_client, None, mock_queue)

    assert mock_model_client.complete_json.call_count == 4
    
    # Check that update_job with status=complete was called
    # (In the new pipeline we use update_job instead of set_result)
    mock_queue.update_job.assert_called()
    
    # Find the call that sets status to "complete"
    complete_call = None
    for call in mock_queue.update_job.mock_calls:
        if call.kwargs.get("status") == "complete":
            complete_call = call
            break
            
    assert complete_call is not None
    job_id = complete_call.kwargs.get("job_id") or complete_call.args[0]
    assert job_id == "job123"
    result = complete_call.kwargs["result"]
    assert result["total_llm_calls"] == 4
    assert result["verdict"]["resilience_score"] == 68

@pytest.mark.asyncio
async def test_structure_extraction_retry(mock_model_client, mock_queue):
    mock_model_client.complete_json.side_effect = [
        ValueError("JSON Parse Error"), # First call fails
        {
            "main_claim": "AI will replace jobs",
            "assumptions": ["assumption 1", "assumption 2"]
        },
        {
            "best_defense": "This is the best defense text, which is longer than twenty characters.",
            "supporting_points": ["point 1"]
        },
        {
            "strongest_attack": "This is the strongest attack text, which is also longer than twenty chars.",
            "counterpoints": ["counter 1"]
        },
        {
            "resilience_score": 68,
            "verdict": "Strong results",
            "score_explanation": "Summary of reasoning.",
            "score_breakdown": {
                "evidence_quality": {"score": 14, "reason": "reason"},
                "assumption_strength": {"score": 14, "reason": "reason"},
                "counterargument_resistance": {"score": 14, "reason": "reason"},
                "practical_feasibility": {"score": 13, "reason": "reason"},
                "scope_precision": {"score": 13, "reason": "reason"}
            },
            "critical_vulnerability": "The main vulnerability.",
            "recommended_revision": "A much better claim.",
            "recommended_fixes": ["fix 1"]
        }
    ]

    await run_analysis("job123", "Some argument", mock_model_client, None, mock_queue)

    # 1 failed call + 1 retry + Defense + Attack + Judge = 5 calls total
    assert mock_model_client.complete_json.call_count == 5
