from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
import uuid
from datetime import datetime, timezone

from models.schemas import AnalysisRequest, AnalysisJob
from agents.pipeline import run_analysis

router = APIRouter()

@router.post("")
async def start_analysis(req: AnalysisRequest, request: Request, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        job_id=job_id,
        status="pending",
        current_step=1,
        current_step_label="Queued...",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    queue = request.app.state.job_queue
    await queue.create_job(job)
    
    background_tasks.add_task(
        run_analysis,
        job_id=job_id,
        argument=req.argument,
        model_client=request.app.state.model_client,
        foundry_client=None,
        queue=queue
    )
    
    return {"job_id": job_id, "status": "pending", "message": "Analysis started"}

@router.get("/status/{job_id}")
async def get_analysis_status(job_id: str, request: Request):
    queue = request.app.state.job_queue
    job = await queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/result/{job_id}")
async def get_analysis_result(job_id: str, request: Request):
    queue = request.app.state.job_queue
    job = await queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status == "complete":
        return job.result
    elif job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error_message or "Job failed")
    else:
        return JSONResponse(status_code=202, content={"message": "Still processing"})

from fastapi.responses import JSONResponse
