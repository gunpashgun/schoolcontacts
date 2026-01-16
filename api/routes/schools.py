"""
School processing API routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import Optional
import base64
import uuid
from datetime import datetime

from api.models.api_models import (
    ProcessRequest, ProcessResponse, JobStatusResponse,
    ResultsResponse, SchoolResultResponse, DownloadResponse
)
from api.services.parser import InputParser
from api.services.enrichment import EnrichmentService
from api.database.supabase import SupabaseDB
from models import SchoolInput, PersonLead, ProcessingStatus

router = APIRouter(prefix="/api/schools", tags=["schools"])

# In-memory job storage (in production, use Redis or database)
jobs = {}
db = SupabaseDB()
enrichment_service = EnrichmentService()


async def process_schools_background(job_id: str, schools: list):
    """Background task to process schools"""
    try:
        await db.update_job_status(job_id, "processing")
        
        school_inputs = [SchoolInput(**s) if isinstance(s, dict) else s for s in schools]
        results = await enrichment_service.process_schools(
            school_inputs,
            progress_callback=lambda processed, total, result: update_progress(job_id, processed, total, result)
        )
        
        # Save results to database
        successful = 0
        failed = 0
        
        for result in results:
            if result.status.value == "completed" and result.school_data:
                # Save school result
                school_dict = result.school_data.model_dump()
                await db.save_school_result(job_id, school_dict)
                
                # Save person leads
                person_leads = []
                for dm in result.school_data.decision_makers:
                    if dm.name:
                        lead = PersonLead.from_decision_maker(dm, result.school_data)
                        person_leads.append(lead.model_dump())
                
                if person_leads:
                    await db.save_person_leads(job_id, person_leads)
                
                successful += 1
            else:
                failed += 1
        
        await db.update_job_progress(job_id, len(results), successful, failed)
        await db.update_job_status(job_id, "completed")
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = results
        
    except Exception as e:
        await db.update_job_status(job_id, "failed", str(e))
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def update_progress(job_id: str, processed: int, total: int, result):
    """Update job progress"""
    await db.update_job_progress(
        job_id,
        processed,
        sum(1 for _ in range(processed) if result.status.value == "completed"),
        sum(1 for _ in range(processed) if result.status.value == "failed")
    )


@router.post("/process", response_model=ProcessResponse)
async def process_schools(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """Process schools from input"""
    try:
        # Parse schools
        if request.format == "excel":
            # For Excel, we need file upload
            raise HTTPException(status_code=400, detail="Use /process/file endpoint for Excel files")
        
        schools = InputParser.parse(request.schools or "", request.format)
        
        if not schools:
            raise HTTPException(status_code=400, detail="No schools found in input")
        
        # Create job
        job_id = str(uuid.uuid4())
        await db.create_job(None, request.format, len(schools))
        
        # Store job info
        jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "schools_count": len(schools),
            "schools": [s.model_dump() for s in schools],
            "created_at": datetime.now()
        }
        
        # Start background processing
        background_tasks.add_task(process_schools_background, job_id, schools)
        
        return ProcessResponse(
            job_id=job_id,
            status="pending",
            schools_count=len(schools),
            message=f"Processing {len(schools)} schools"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/file", response_model=ProcessResponse)
async def process_schools_file(
    file: UploadFile = File(...),
    format_type: str = "auto",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Process schools from uploaded file"""
    try:
        content = await file.read()
        
        # Detect format
        if format_type == "auto":
            if file.filename.endswith('.csv'):
                format_type = "csv"
            elif file.filename.endswith('.json'):
                format_type = "json"
            elif file.filename.endswith(('.xlsx', '.xls')):
                format_type = "excel"
            else:
                format_type = "text"
        
        # Parse
        if format_type == "excel":
            schools = InputParser.parse_excel(content)
        elif format_type == "csv":
            schools = InputParser.parse_csv(content.decode('utf-8'))
        elif format_type == "json":
            schools = InputParser.parse_json(content.decode('utf-8'))
        else:
            schools = InputParser.parse_text(content.decode('utf-8'))
        
        if not schools:
            raise HTTPException(status_code=400, detail="No schools found in file")
        
        # Create job
        job_id = str(uuid.uuid4())
        await db.create_job(None, format_type, len(schools))
        
        jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "schools_count": len(schools),
            "schools": [s.model_dump() for s in schools],
            "created_at": datetime.now()
        }
        
        # Start background processing
        background_tasks.add_task(process_schools_background, job_id, schools)
        
        return ProcessResponse(
            job_id=job_id,
            status="pending",
            schools_count=len(schools),
            message=f"Processing {len(schools)} schools from {file.filename}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job processing status"""
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


@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """Get processing results"""
    job = await db.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    results_data = await db.get_job_results(job_id)
    
    schools = []
    for school_data in results_data["schools"]:
        verified = sum(
            1 for lead in results_data["person_leads"]
            if lead.get("school_name") == school_data.get("school_name")
            and (lead.get("whatsapp_verified") or lead.get("email_verified"))
        )
        
        schools.append(SchoolResultResponse(
            school_name=school_data.get("school_name", ""),
            school_type=school_data.get("school_type", ""),
            location=school_data.get("location", ""),
            foundation_name=school_data.get("foundation_name"),
            npsn=school_data.get("npsn"),
            official_website=school_data.get("official_website"),
            official_email=school_data.get("official_email"),
            whatsapp_business=school_data.get("whatsapp_business"),
            data_quality_score=school_data.get("data_quality_score", 0),
            decision_makers_count=len(school_data.get("decision_makers", [])),
            verified_contacts=verified
        ))
    
    return ResultsResponse(
        job_id=job_id,
        total_schools=job.get("schools_count", 0),
        successful=job.get("successful_count", 0),
        failed=job.get("failed_count", 0),
        schools=schools
    )


@router.get("/download/{job_id}")
async def download_results(job_id: str, format: str = "csv"):
    """Download results as file"""
    from fastapi.responses import FileResponse
    from main import LeadEnrichmentEngine
    import tempfile
    import os
    
    job = await db.get_job(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    results_data = await db.get_job_results(job_id)
    
    # Reconstruct ProcessingResult objects (simplified)
    # In production, store full results or reconstruct from DB
    
    # For now, return a placeholder
    # In production, use the engine to export
    engine = LeadEnrichmentEngine()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp:
        # Export logic here (simplified)
        filename = tmp.name
    
    return FileResponse(
        filename,
        media_type="application/octet-stream",
        filename=f"leads_{job_id}.{format}"
    )

