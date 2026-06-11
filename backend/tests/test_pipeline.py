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
        # Defense
        {
            "best_defense": "Best defense text.",
            "supporting_points": ["point 1", "point 2"]
        },
        # Prosecutor
        {
            "strongest_attack": "Strongest attack text.",
            "counterpoints": ["counter 1", "counter 2"]
        },
        # Judge
        {
            "resilience_score": 68,
            "verdict": "Mixed results",
            "critical_vulnerability": "The main vulnerability.",
            "recommended_fixes": ["fix 1", "fix 2", "fix 3"],
            "stronger_version": "A much better claim.",
            "reasoning_summary": "Summary of reasoning."
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
    assert complete_call.kwargs["job_id"] == "job123"
    result = complete_call.kwargs["result"]
    assert result["total_llm_calls"] == 4
    assert result["verdict"]["resilience_score"] == 68

@pytest.mark.asyncio
async def test_structure_extraction_retry(mock_model_client, mock_queue):
    mock_model_client.complete_json.side_effect = [
        Exception("JSON Parse Error"), # First call fails
        {
            "main_claim": "AI will replace jobs",
            "assumptions": ["assumption 1", "assumption 2"]
        },
        {
            "best_defense": "Best defense text.",
            "supporting_points": ["point 1"]
        },
        {
            "strongest_attack": "Strongest attack text.",
            "counterpoints": ["counter 1"]
        },
        {
            "resilience_score": 68,
            "verdict": "Mixed results",
            "critical_vulnerability": "The main vulnerability.",
            "recommended_fixes": ["fix 1"],
            "stronger_version": "A much better claim.",
            "reasoning_summary": "Summary of reasoning."
        }
    ]

    await run_analysis("job123", "Some argument", mock_model_client, None, mock_queue)

    # 1 failed call + 1 retry + Defense + Attack + Judge = 5 calls total
    assert mock_model_client.complete_json.call_count == 5
