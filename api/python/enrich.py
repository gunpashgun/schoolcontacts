"""
Vercel Python Serverless Function for school enrichment
"""
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import SchoolInput, ProcessingResult, ProcessingStatus
from main import LeadEnrichmentEngine
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def enrich_schools_async(schools_data: list, job_id: str):
    """
    Enrich schools asynchronously and save to Supabase
    
    Args:
        schools_data: List of school dicts with name, type, location
        job_id: Job ID from Supabase
    """
    try:
        from api.database.supabase import SupabaseDB
        
        db = SupabaseDB()
        engine = LeadEnrichmentEngine()
        
        # Update job status to processing
        await db.update_job_status(job_id, "processing")
        
        successful = 0
        failed = 0
        
        for i, school_dict in enumerate(schools_data):
            try:
                school = SchoolInput(**school_dict)
                
                # Process school
                result = await engine.enrich_school(school)
                
                if result.status == ProcessingStatus.COMPLETED and result.school_data:
                    # Save school result
                    school_dict = result.school_data.model_dump()
                    await db.save_school_result(job_id, school_dict)
                    
                    # Save person leads
                    person_leads = []
                    for dm in result.school_data.decision_makers:
                        if dm.name:
                            from models import PersonLead
                            lead = PersonLead.from_decision_maker(dm, result.school_data)
                            person_leads.append(lead.model_dump())
                    
                    if person_leads:
                        await db.save_person_leads(job_id, person_leads)
                    
                    successful += 1
                else:
                    failed += 1
                
                # Update progress
                await db.update_job_progress(job_id, i + 1, successful, failed)
                
            except Exception as e:
                logger.error(f"Error processing {school_dict.get('name', 'unknown')}: {e}")
                failed += 1
                await db.update_job_progress(job_id, i + 1, successful, failed)
        
        # Mark as completed
        await db.update_job_status(job_id, "completed")
        
        return {
            "success": True,
            "processed": len(schools_data),
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Enrichment error: {e}")
        await db.update_job_status(job_id, "failed", str(e))
        raise


def handler(request):
    """
    Vercel Python serverless function handler
    
    Expected request body:
    {
        "job_id": "uuid",
        "schools": [
            {"name": "...", "type": "...", "location": "..."}
        ]
    }
    """
    try:
        # Parse request
        if hasattr(request, 'json'):
            body = request.json
        else:
            body = json.loads(request.body) if hasattr(request, 'body') else {}
        
        job_id = body.get('job_id')
        schools = body.get('schools', [])
        
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'job_id is required'})
            }
        
        if not schools:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'schools array is required'})
            }
        
        # Run async enrichment
        result = asyncio.run(enrich_schools_async(schools, job_id))
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

