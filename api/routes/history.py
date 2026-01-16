"""
History API routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from api.database.supabase import SupabaseDB
from api.models.api_models import JobStatusResponse

router = APIRouter(prefix="/api/history", tags=["history"])
db = SupabaseDB()


@router.get("/", response_model=List[JobStatusResponse])
async def get_history(user_id: Optional[str] = None, limit: int = 50):
    """Get job history"""
    jobs = await db.get_job_history(user_id, limit)
    
    return [
        JobStatusResponse(
            job_id=job["id"],
            status=job.get("status", "pending"),
            schools_count=job.get("schools_count", 0),
            processed_count=job.get("processed_count", 0),
            successful_count=job.get("successful_count", 0),
            failed_count=job.get("failed_count", 0),
            created_at=job.get("created_at"),
            completed_at=job.get("completed_at"),
            error_message=job.get("error_message")
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    """Get specific job"""
    job = await db.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job.get("status", "pending"),
        schools_count=job.get("schools_count", 0),
        processed_count=job.get("processed_count", 0),
        successful_count=job.get("successful_count", 0),
        failed_count=job.get("failed_count", 0),
        created_at=job.get("created_at"),
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message")
    )

