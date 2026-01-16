"""
Wrapper for LeadEnrichmentEngine to work with API
"""
import asyncio
from typing import List
from models import SchoolInput, ProcessingResult
from main import LeadEnrichmentEngine
import logging

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for school enrichment"""
    
    def __init__(self):
        self.engine = LeadEnrichmentEngine()
    
    async def process_schools(
        self,
        schools: List[SchoolInput],
        progress_callback=None
    ) -> List[ProcessingResult]:
        """
        Process schools with optional progress callback
        
        Args:
            schools: List of schools to process
            progress_callback: Optional callback(job_id, processed, total, result)
        """
        results = []
        
        for i, school in enumerate(schools):
            try:
                result = await self.engine.enrich_school(school)
                results.append(result)
                
                if progress_callback:
                    await progress_callback(i + 1, len(schools), result)
                
            except Exception as e:
                logger.error(f"Error processing {school.name}: {e}")
                results.append(ProcessingResult(
                    school_input=school,
                    status="failed",
                    error_message=str(e)
                ))
        
        return results

