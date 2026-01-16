"""
Supabase client and database operations
"""
import os
from typing import Optional, List, Dict
from supabase import create_client, Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase database client"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        # Use service role key for backend (bypasses RLS)
        # For frontend, use SUPABASE_ANON_KEY
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url:
            raise ValueError("SUPABASE_URL must be set")
        
        if not supabase_key:
            raise ValueError("SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def create_job(
        self,
        user_id: Optional[str],
        input_format: str,
        schools_count: int
    ) -> str:
        """Create a new job and return job ID"""
        result = self.client.table("jobs").insert({
            "user_id": user_id,
            "input_format": input_format,
            "schools_count": schools_count,
            "status": "pending",
            "processed_count": 0,
            "successful_count": 0,
            "failed_count": 0
        }).execute()
        
        if result.data:
            return result.data[0]["id"]
        raise Exception("Failed to create job")
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update job status"""
        update_data = {"status": status}
        if status == "completed":
            update_data["completed_at"] = datetime.now().isoformat()
        if error_message:
            update_data["error_message"] = error_message
        
        self.client.table("jobs").update(update_data).eq("id", job_id).execute()
    
    async def update_job_progress(
        self,
        job_id: str,
        processed_count: int,
        successful_count: int,
        failed_count: int
    ):
        """Update job progress"""
        self.client.table("jobs").update({
            "processed_count": processed_count,
            "successful_count": successful_count,
            "failed_count": failed_count
        }).eq("id", job_id).execute()
    
    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        result = self.client.table("jobs").select("*").eq("id", job_id).execute()
        if result.data:
            return result.data[0]
        return None
    
    async def save_school_result(self, job_id: str, school_data: Dict):
        """Save school result"""
        self.client.table("school_results").insert({
            "job_id": job_id,
            "school_name": school_data.get("school_name"),
            "school_type": school_data.get("school_type"),
            "location": school_data.get("location"),
            "npsn": school_data.get("npsn"),
            "foundation_name": school_data.get("foundation_name"),
            "official_website": school_data.get("official_website"),
            "official_email": school_data.get("official_email"),
            "whatsapp_business": school_data.get("whatsapp_business"),
            "data_quality_score": school_data.get("data_quality_score", 0),
            "decision_makers": school_data.get("decision_makers", []),
            "tech_stack": school_data.get("tech_stack", [])
        }).execute()
    
    async def save_person_leads(self, job_id: str, person_leads: List[Dict]):
        """Save person leads"""
        if not person_leads:
            return
        
        self.client.table("person_leads").insert([
            {
                "job_id": job_id,
                "school_name": lead.get("school_name"),
                "person_name": lead.get("person_name"),
                "role": lead.get("role"),
                "role_indonesian": lead.get("role_indonesian"),
                "priority_tier": lead.get("priority_tier"),
                "direct_whatsapp": lead.get("direct_whatsapp"),
                "whatsapp_verified": lead.get("whatsapp_verified", False),
                "direct_email": lead.get("direct_email"),
                "email_verified": lead.get("email_verified", False),
                "email_is_personal": lead.get("email_is_personal", False),
                "linkedin": lead.get("linkedin"),
                "tech_stack": lead.get("tech_stack"),
                "source_url": lead.get("source_url"),
                "confidence": lead.get("confidence", 0)
            }
            for lead in person_leads
        ]).execute()
    
    async def get_job_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get job history"""
        query = self.client.table("jobs").select("*").order("created_at", desc=True).limit(limit)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        return result.data if result.data else []
    
    async def get_job_results(self, job_id: str) -> Dict:
        """Get all results for a job"""
        # Get school results
        school_results = self.client.table("school_results").select("*").eq("job_id", job_id).execute()
        
        # Get person leads
        person_leads = self.client.table("person_leads").select("*").eq("job_id", job_id).execute()
        
        return {
            "schools": school_results.data if school_results.data else [],
            "person_leads": person_leads.data if person_leads.data else []
        }

