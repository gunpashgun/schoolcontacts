"""
Pydantic models for structured data in Indonesia EdTech Lead Gen Engine
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum
from datetime import datetime
import re


class SchoolType(str, Enum):
    """Types of schools in Indonesia"""
    PRIVATE_CHRISTIAN = "Private Christian"
    PRIVATE_CATHOLIC = "Private Catholic"
    PRIVATE_ISLAMIC = "Private Islamic"
    PRIVATE_BUDDHIST = "Private Buddhist"
    PRIVATE_NATIONAL = "Private National"
    PRIVATE_NATIONAL_PLUS = "Private National Plus"
    INTERNATIONAL = "International"
    PUBLIC = "Public"
    HYBRID = "Private/Hybrid"
    PRESCHOOL = "Preschool"
    ENRICHMENT = "Enrichment"
    OTHER = "Other"


class RolePriority(str, Enum):
    """Priority levels for decision makers"""
    HIGHEST = "highest"      # Ketua Yayasan
    HIGH = "high"            # Pembina, Direktur
    MEDIUM = "medium"        # Kepala Sekolah
    LOW = "low"              # Wakil, Bendahara
    LOWEST = "lowest"        # Other staff


# ===========================================
# Input Models
# ===========================================

class SchoolInput(BaseModel):
    """Input model for a school to process"""
    name: str
    type: str
    location: str
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "PPPK Petra",
                "type": "Private Christian",
                "location": "Surabaya",
                "notes": "Elementary to High School, Education Board/Group"
            }
        }


# ===========================================
# Contact Models
# ===========================================

class PhoneNumber(BaseModel):
    """Validated Indonesian phone number"""
    raw: str                           # Original format
    normalized: str                    # +62 format
    is_mobile: bool = False
    is_whatsapp: bool = False
    source_url: Optional[str] = None
    
    @field_validator('normalized')
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalize phone number to +62 format"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Convert to +62 format
        if cleaned.startswith('08'):
            return '+62' + cleaned[1:]
        elif cleaned.startswith('62'):
            return '+' + cleaned
        elif cleaned.startswith('+62'):
            return cleaned
        
        return cleaned


class DecisionMaker(BaseModel):
    """A decision maker at a school or foundation"""
    name: Optional[str] = None
    role: Optional[str] = None                    # English role
    role_indonesian: Optional[str] = None         # Indonesian role (e.g., Ketua Yayasan)
    priority: RolePriority = RolePriority.LOWEST
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None                # WhatsApp number (prioritized)
    
    # NEW: Verification status
    whatsapp_verified: bool = False
    email_verified: bool = False
    email_is_personal: bool = False  # True if personal, False if general (info@, admin@)
    
    # Social profiles
    linkedin_url: Optional[str] = None
    
    # Metadata
    source_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @field_validator('whatsapp')
    @classmethod
    def normalize_whatsapp(cls, v: Optional[str]) -> Optional[str]:
        """Normalize WhatsApp number to +62 format"""
        if not v:
            return None
        
        # Extract from wa.me links
        wa_me_match = re.search(r'wa\.me/(\d+)', v)
        if wa_me_match:
            return '+' + wa_me_match.group(1)
        
        # Extract from api.whatsapp.com links
        api_match = re.search(r'phone=(\d+)', v)
        if api_match:
            return '+' + api_match.group(1)
        
        # Normalize direct number
        cleaned = re.sub(r'[^\d+]', '', v)
        if cleaned.startswith('08'):
            return '+62' + cleaned[1:]
        elif cleaned.startswith('62'):
            return '+' + cleaned
        elif cleaned.startswith('+62'):
            return cleaned
        
        return v
    
    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin(cls, v: Optional[str]) -> Optional[str]:
        """Validate LinkedIn URL"""
        if not v:
            return None
        if 'linkedin.com' not in v.lower():
            return None
        return v


# ===========================================
# School Data Models
# ===========================================

class SchoolData(BaseModel):
    """Complete enriched data for a school"""
    
    # Basic information
    school_name: str
    school_type: str
    location: str
    
    # Official identifiers (Indonesian Ministry of Education)
    npsn: Optional[str] = None           # Nomor Pokok Sekolah Nasional (8 digits)
    npyp: Optional[str] = None           # Nomor Pokok Yayasan Pendidikan
    
    # Foundation information
    foundation_name: Optional[str] = None
    foundation_established: Optional[str] = None
    
    # Decision makers (sorted by priority)
    decision_makers: List[DecisionMaker] = []
    
    # Primary contacts
    official_website: Optional[str] = None
    official_email: Optional[str] = None
    whatsapp_business: Optional[str] = None     # Primary WhatsApp for business
    phone_numbers: List[str] = []
    
    # Social media
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    youtube: Optional[str] = None
    
    # Tech stack (NEW: LMS/EdTech platforms detected)
    tech_stack: List[str] = []              # e.g., ["canvas", "google_classroom"]
    
    # Metadata
    source_urls: List[str] = []
    last_updated: Optional[str] = None
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_notes: Optional[str] = None
    
    @field_validator('npsn')
    @classmethod
    def validate_npsn(cls, v: Optional[str]) -> Optional[str]:
        """Validate NPSN is 8 digits"""
        if not v:
            return None
        cleaned = re.sub(r'\D', '', v)
        if len(cleaned) == 8:
            return cleaned
        return None
    
    def get_primary_whatsapp(self) -> Optional[str]:
        """Get the best WhatsApp number available"""
        # First, check whatsapp_business
        if self.whatsapp_business:
            return self.whatsapp_business
        
        # Then check decision makers
        for dm in self.decision_makers:
            if dm.whatsapp:
                return dm.whatsapp
        
        return None
    
    def get_primary_contact(self) -> Optional[DecisionMaker]:
        """Get the highest priority decision maker with contact info"""
        for dm in sorted(self.decision_makers, key=lambda x: list(RolePriority).index(x.priority)):
            if dm.whatsapp or dm.email or dm.phone:
                return dm
        return None
    
    def calculate_quality_score(self) -> float:
        """Calculate data quality score with verification bonus"""
        score = 0.0
        total_weight = 0.0
        
        # Base weights
        checks = [
            (bool(self.foundation_name), 0.1),
            (bool(self.npsn), 0.1),
            (bool(self.official_website), 0.1),
            (bool(self.official_email), 0.15),
            (bool(self.whatsapp_business), 0.2),        # High priority
            (len(self.decision_makers) > 0, 0.15),
            (any(dm.whatsapp for dm in self.decision_makers), 0.1),
            (any(dm.linkedin_url for dm in self.decision_makers), 0.05),
            (bool(self.instagram), 0.025),
            (bool(self.facebook), 0.025),
        ]
        
        for check, weight in checks:
            total_weight += weight
            if check:
                score += weight
        
        # NEW: Verification bonus (+30% if both WA and Email verified)
        verified_contacts = sum(
            1 for dm in self.decision_makers
            if dm.whatsapp_verified and dm.email_verified
        )
        if verified_contacts > 0:
            verification_bonus = min(0.3, verified_contacts * 0.1)
            score += verification_bonus
            total_weight += verification_bonus
        
        self.data_quality_score = round(score / total_weight, 2) if total_weight > 0 else 0.0
        return self.data_quality_score


# ===========================================
# Search & Scraping Models
# ===========================================

class SearchResult(BaseModel):
    """A single search result from Serper API"""
    query: str
    url: str
    title: str
    snippet: str
    position: int
    
    def is_linkedin(self) -> bool:
        return 'linkedin.com' in self.url.lower()
    
    def is_official_domain(self) -> bool:
        """Check if result is from official Indonesian education domain"""
        official_domains = ['kemdikbud.go.id', '.sch.id', '.ac.id']
        return any(domain in self.url.lower() for domain in official_domains)


class ScrapedPage(BaseModel):
    """Content from a scraped web page"""
    url: str
    title: str
    html_content: str
    text_content: str                    # Clean text or markdown
    links: List[str] = []
    success: bool = True
    error: Optional[str] = None
    scraped_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def is_priority_page(self, priority_keywords: List[str]) -> bool:
        """Check if this is a priority page based on URL"""
        url_lower = self.url.lower()
        return any(kw in url_lower for kw in priority_keywords)


# ===========================================
# Processing Models
# ===========================================

class ProcessingStatus(str, Enum):
    """Status of school processing"""
    PENDING = "pending"
    SEARCHING = "searching"
    SCRAPING = "scraping"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingResult(BaseModel):
    """Result of processing a single school"""
    school_input: SchoolInput
    school_data: Optional[SchoolData] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    search_results_count: int = 0
    pages_scraped: int = 0


class BatchResult(BaseModel):
    """Result of processing a batch of schools"""
    total_schools: int
    successful: int
    failed: int
    results: List[ProcessingResult]
    started_at: str
    completed_at: Optional[str] = None
    total_time_seconds: float = 0.0


# ===========================================
# Person-Centric Lead Model (NEW)
# ===========================================

class PersonLead(BaseModel):
    """
    Person-centric lead for export
    One row per person (not per school)
    
    This is the final output format optimized for B2B outreach
    """
    # School/Foundation context
    school_name: str
    foundation_name: Optional[str] = None
    school_type: str = ""
    location: str = ""
    
    # Person information
    person_name: str
    role: str                               # English role
    role_indonesian: Optional[str] = None   # Indonesian role (Bahasa)
    priority_tier: int = 5                  # 1 = highest (Ketua Yayasan), 5 = lowest
    
    # Direct contacts (specific to this person)
    direct_whatsapp: Optional[str] = None
    direct_email: Optional[str] = None
    linkedin: Optional[str] = None
    
    # Tech context (for EdTech sales)
    tech_stack: str = ""                    # Comma-separated LMS list
    
    # Source tracking
    source_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @classmethod
    def from_decision_maker(
        cls,
        dm: DecisionMaker,
        school_data: 'SchoolData'
    ) -> 'PersonLead':
        """Create PersonLead from DecisionMaker and SchoolData"""
        # Determine priority tier from role priority
        tier_map = {
            RolePriority.HIGHEST: 1,
            RolePriority.HIGH: 2,
            RolePriority.MEDIUM: 3,
            RolePriority.LOW: 4,
            RolePriority.LOWEST: 5,
        }
        
        return cls(
            school_name=school_data.school_name,
            foundation_name=school_data.foundation_name,
            school_type=school_data.school_type,
            location=school_data.location,
            person_name=dm.name or "Unknown",
            role=dm.role or "",
            role_indonesian=dm.role_indonesian,
            priority_tier=tier_map.get(dm.priority, 5),
            direct_whatsapp=dm.whatsapp,
            direct_email=dm.email,
            linkedin=dm.linkedin_url,
            tech_stack=", ".join(school_data.tech_stack) if school_data.tech_stack else "",
            source_url=dm.source_url,
            confidence=dm.confidence,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV/DataFrame export"""
        return {
            "School Name": self.school_name,
            "Foundation": self.foundation_name or "",
            "School Type": self.school_type,
            "Location": self.location,
            "Person Name": self.person_name,
            "Role": self.role,
            "Role (Indonesian)": self.role_indonesian or "",
            "Priority Tier": self.priority_tier,
            "Direct WhatsApp": self.direct_whatsapp or "",
            "Direct Email": self.direct_email or "",
            "LinkedIn": self.linkedin or "",
            "Tech Stack": self.tech_stack,
            "Source URL": self.source_url or "",
            "Confidence": self.confidence,
        }


# ===========================================
# Foundation Clustering (NEW)
# ===========================================

class FoundationCluster(BaseModel):
    """
    Cluster of schools under the same foundation/Yayasan
    
    Used for B2B strategy - reaching one foundation can open doors to all schools
    """
    foundation_name: str
    foundation_type: Optional[str] = None   # e.g., "Religious", "Education Group"
    schools: List[str] = []                 # School names under this foundation
    total_schools: int = 0
    
    # Key contacts at foundation level
    foundation_contacts: List[PersonLead] = []
    
    # Aggregated stats
    total_decision_makers: int = 0
    has_whatsapp: bool = False
    has_linkedin: bool = False
    
    # Common tech stack across schools
    common_tech_stack: List[str] = []

