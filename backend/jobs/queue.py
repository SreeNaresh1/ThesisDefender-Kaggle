import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from datetime import datetime, timezone

from models.schemas import AnalysisJob, ArgumentAnalysis

logger = logging.getLogger(__name__)

class JobQueue:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.in_memory_store = {}

    async def connect(self):
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable \u2014 using in-memory job store. Error: {str(e)}")
            self.redis = None

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def create_job(self, job: AnalysisJob) -> str:
        if self.redis:
            try:
                await self.redis.setex(f"job:{job.job_id}", 43200, job.model_dump_json())
                return job.job_id
            except Exception:
                pass
        
        self.in_memory_store[job.job_id] = job.model_dump_json()
        return job.job_id

    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        data = None
        if self.redis:
            try:
                data = await self.redis.get(f"job:{job_id}")
            except Exception:
                pass
        
        if data is None:
            data = self.in_memory_store.get(job_id)
            
        if data:
            return AnalysisJob.model_validate_json(data)
        return None

    async def update_job(self, job_id: str, **kwargs) -> None:
        job = await self.get_job(job_id)
        if not job:
            return
            
        job_dict = job.model_dump()
        for k, v in kwargs.items():
            job_dict[k] = v
        job_dict['updated_at'] = datetime.now(timezone.utc)
        
        updated_job = AnalysisJob.model_validate(job_dict)
        
        if self.redis:
            try:
                await self.redis.setex(f"job:{job_id}", 43200, updated_job.model_dump_json())
                return
            except Exception:
                pass
                
        self.in_memory_store[job_id] = updated_job.model_dump_json()

    async def set_result(self, job_id: str, result: ArgumentAnalysis) -> None:
        await self.update_job(
            job_id,
            status="complete",
            result=result.model_dump(),
            current_step=3,
            current_step_label="Complete"
        )
