"""
Vercel Python Serverless Function for school enrichment
Vercel automatically recognizes .py files in api/ directory as serverless functions
"""
import json
import sys
import os
from pathlib import Path

# Add project root to path to import Python modules
# When deployed on Vercel, the working directory is the project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set environment variables from Vercel
if os.getenv('VERCEL'):
    # Load from Vercel environment
    pass

from models import SchoolInput, ProcessingResult, ProcessingStatus
from main import LeadEnrichmentEngine
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def enrich_schools_async(schools_data: list, job_id: str):
    """
    Enrich schools asynchronously and save to Supabase
    """
    try:
        # Import after path is set
        try:
            from api.database.supabase import SupabaseDB
        except ImportError:
            # Fallback: try direct import
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from api.database.supabase import SupabaseDB
        
        db = SupabaseDB()
        engine = LeadEnrichmentEngine()
        
        await db.update_job_status(job_id, "processing")
        
        successful = 0
        failed = 0
        
        for i, school_dict in enumerate(schools_data):
            try:
                school = SchoolInput(**school_dict)
                result = await engine.enrich_school(school)
                
                if result.status == ProcessingStatus.COMPLETED and result.school_data:
                    school_dict = result.school_data.model_dump()
                    await db.save_school_result(job_id, school_dict)
                    
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
                
                await db.update_job_progress(job_id, i + 1, successful, failed)
                
            except Exception as e:
                logger.error(f"Error processing school: {e}")
                failed += 1
                await db.update_job_progress(job_id, i + 1, successful, failed)
        
        await db.update_job_status(job_id, "completed")
        
        return {
            "success": True,
            "processed": len(schools_data),
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Enrichment error: {e}")
        try:
            await db.update_job_status(job_id, "failed", str(e))
        except:
            pass
        raise


def handler(request):
    """
    Vercel Python serverless function handler
    """
    try:
        # Parse request body
        if hasattr(request, 'json'):
            body = request.json
        elif hasattr(request, 'body'):
            body = json.loads(request.body) if isinstance(request.body, str) else request.body
        else:
            body = {}
        
        job_id = body.get('job_id')
        schools = body.get('schools', [])
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'job_id is required'})
            }
        
        if not schools:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'schools array is required'})
            }
        
        # Run async enrichment
        result = asyncio.run(enrich_schools_async(schools, job_id))
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

