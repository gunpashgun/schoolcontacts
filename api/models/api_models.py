"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class ProcessRequest(BaseModel):
    """Request to process schools"""
    schools: Optional[str] = None  # Text input
    format: Literal["text", "csv", "json", "excel"] = "text"
    file_content: Optional[str] = None  # Base64 encoded file content (for Excel/CSV)


class ProcessResponse(BaseModel):
    """Response with job ID"""
    job_id: str
    status: str = "pending"
    schools_count: int
    message: str


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    schools_count: int
    processed_count: int
    successful_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SchoolResultResponse(BaseModel):
    """Single school result"""
    school_name: str
    school_type: str
    location: str
    foundation_name: Optional[str] = None
    npsn: Optional[str] = None
    official_website: Optional[str] = None
    official_email: Optional[str] = None
    whatsapp_business: Optional[str] = None
    data_quality_score: float
    decision_makers_count: int
    verified_contacts: int


class ResultsResponse(BaseModel):
    """Results response"""
    job_id: str
    total_schools: int
    successful: int
    failed: int
    schools: List[SchoolResultResponse]


class DownloadResponse(BaseModel):
    """Download response"""
    download_url: str
    filename: str
    format: str  # csv, excel, json

