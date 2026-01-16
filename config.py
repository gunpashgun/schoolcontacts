"""
Configuration module for Indonesia EdTech Lead Gen Engine
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Main configuration class"""
    
    # ===========================================
    # API Keys
    # ===========================================
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # ===========================================
    # LLM Configuration
    # ===========================================
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # 'openrouter', 'claude', or 'openai'
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # ===========================================
    # Rate Limiting (REDUCED for speed)
    # ===========================================
    REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", 60))
    SCRAPE_DELAY_SECONDS = float(os.getenv("SCRAPE_DELAY_SECONDS", 0.5))
    SCHOOL_DELAY_SECONDS = float(os.getenv("SCHOOL_DELAY_SECONDS", 1))
    
    # ===========================================
    # Scraping Options (REDUCED timeouts)
    # ===========================================
    MAX_PAGES_PER_SCHOOL = int(os.getenv("MAX_PAGES_PER_SCHOOL", 3))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
    HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
    
    # ===========================================
    # Paths
    # ===========================================
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "output"
    
    # ===========================================
    # Indonesian-specific Keywords (Critical for accuracy)
    # ===========================================
    
    # Decision maker roles in Indonesian - EXPANDED LIST
    ROLE_KEYWORDS = {
        # TIER 1: Foundation Leadership (Ultimate Decision Makers)
        "ketua_yayasan": [
            "Ketua Yayasan",      # Foundation Chairman - HIGHEST PRIORITY
            "Ketua Pengurus",     # Board Chairman
            "Ketua Dewan",        # Board Chairman
            "Chairman",
            "Founder",
            "Pendiri",            # Founder
            "Co-Founder",
            "Owner",
            "Pemilik",
        ],
        "pembina": [
            "Pembina",            # Patron/Supervisor
            "Dewan Pembina",      # Board of Patrons
            "Patron",
            "Board Member",
            "Anggota Dewan",
        ],
        
        # TIER 2: Executive Leadership
        "direktur": [
            "Direktur",           # Director
            "Direktur Pendidikan",# Director of Education
            "Direktur Utama",     # Main Director
            "Direktur Eksekutif", # Executive Director
            "Director",
            "Managing Director",
            "Executive Director",
            "CEO",
            "Chief Executive",
        ],
        "kepala_sekolah": [
            "Kepala Sekolah",     # School Principal
            "Principal",
            "Head of School",
            "School Director",
            "Headmaster",
            "Headmistress",
            "School Head",
            "Kepala SD",          # Elementary Principal
            "Kepala SMP",         # Junior High Principal
            "Kepala SMA",         # Senior High Principal
            "Kepala TK",          # Kindergarten Principal
        ],
        
        # TIER 3: Academic Leadership (ADDED)
        "academic": [
            "Academic Coordinator",
            "Koordinator Akademik",
            "Academic Director",
            "Direktur Akademik",
            "Head of Academics",
            "Kepala Bidang Akademik",
            "Curriculum Coordinator",
            "Koordinator Kurikulum",
            "Academic Manager",
            "Dean",
            "Dekan",
            "Head of Curriculum",
            "Kepala Kurikulum",
            "VP Academics",
            "Vice Principal Academics",
        ],
        
        # TIER 4: Department Heads (ADDED)
        "department_head": [
            "Head of Department",
            "Kepala Departemen",
            "Department Head",
            "Division Head",
            "Kepala Divisi",
            "Program Director",
            "Direktur Program",
            "Head of Primary",
            "Head of Secondary",
            "Head of Early Years",
            "Kepala Unit",
            "Unit Head",
            "Section Head",
            "Kepala Bagian",
        ],
        
        # TIER 5: Admissions & Marketing (ADDED - Key for B2B sales)
        "admissions": [
            "Admissions Director",
            "Direktur Admisi",
            "Head of Admissions",
            "Kepala Admisi",
            "Admissions Manager",
            "Manajer Admisi",
            "Admissions Coordinator",
            "Koordinator Admisi",
            "Enrollment Manager",
            "Marketing Director",
            "Direktur Marketing",
            "Head of Marketing",
            "Kepala Marketing",
            "Communications Director",
            "PR Manager",
            "Humas",
        ],
        
        # TIER 6: Operations & Admin
        "wakil_kepala": [
            "Wakil Kepala Sekolah",  # Vice Principal
            "Vice Principal",
            "Deputy Head",
            "Wakil Kepala",
            "Assistant Principal",
            "Deputy Principal",
            "VP Operations",
        ],
        "operations": [
            "Operations Manager",
            "Manajer Operasional",
            "COO",
            "Chief Operating Officer",
            "Head of Operations",
            "Kepala Operasional",
            "School Administrator",
            "Administrator Sekolah",
            "Business Manager",
            "Manajer Bisnis",
            "Finance Manager",
            "Manajer Keuangan",
            "HR Manager",
            "Manajer SDM",
        ],
        "bendahara": [
            "Bendahara",          # Treasurer
            "Treasurer",
            "CFO",
            "Chief Financial Officer",
        ],
        "sekretaris": [
            "Sekretaris",         # Secretary
            "Secretary",
            "Executive Secretary",
            "Sekretaris Eksekutif",
        ],
        
        # TIER 7: IT & Technology (ADDED - Relevant for EdTech)
        "technology": [
            "IT Director",
            "Direktur IT",
            "Head of IT",
            "Kepala IT",
            "Technology Coordinator",
            "Koordinator Teknologi",
            "ICT Coordinator",
            "Koordinator ICT",
            "Digital Learning Coordinator",
            "EdTech Coordinator",
            "CTO",
            "Chief Technology Officer",
            "IT Manager",
            "Manajer IT",
        ],
    }
    
    # Priority order for decision makers (index = priority, lower = more important)
    ROLE_PRIORITY = [
        "ketua_yayasan",
        "pembina", 
        "direktur",
        "kepala_sekolah",
        "academic",          # Academic Coordinator - key for EdTech
        "admission",         # Admissions - key for partnerships
        "it_coordinator",    # IT - key for EdTech products
        "operations",
        "marketing",
        "wakil_kepala",
        "bendahara",
        "sekretaris",
        "teacher_lead",
    ]
    
    # ===========================================
    # Contact Keywords
    # ===========================================
    CONTACT_KEYWORDS = {
        "whatsapp": [
            "wa.me",
            "api.whatsapp.com",
            "WhatsApp",
            "WA:",
            "WA :",
            "Whatsapp:",
        ],
        "phone_indonesia": [
            "+62",           # Country code
            "62",            # Country code without +
            "08",            # Mobile prefix
            "021",           # Jakarta landline
            "031",           # Surabaya landline
            "022",           # Bandung landline
            "024",           # Semarang landline
        ],
        "email": [
            "@",
            "email:",
            "e-mail:",
            "Email:",
            "E-mail:",
        ],
    }
    
    # ===========================================
    # Search Query Templates - EXPANDED
    # ===========================================
    SEARCH_TEMPLATES = {
        # Official Ministry of Education data
        "official_data": 'site:referensi.data.kemdikbud.go.id "{school_name}"',
        
        # NPSN lookup
        "npsn": '"{school_name}" NPSN site:sekolah.data.kemdikbud.go.id',
        
        # LinkedIn search for founders/directors
        "founders_linkedin": '"{school_name}" (Ketua Yayasan OR "Director" OR "Kepala Sekolah" OR "Principal" OR "Founder") site:linkedin.com',
        
        # LinkedIn search for academic/operations staff
        "staff_linkedin": '"{school_name}" ("Academic Coordinator" OR "Admissions" OR "Marketing" OR "IT" OR "Coordinator") site:linkedin.com',
        
        # General contact search
        "contacts": '"{school_name}" (WhatsApp OR "Hubungi kami" OR "Kontak" OR Email)',
        
        # Foundation/organization structure
        "foundation": '"{school_name}" Yayasan (struktur OR organisasi OR pengurus)',
        
        # School website
        "website": '"{school_name}" (official OR resmi) -facebook -instagram -linkedin',
        
        # Location-specific search
        "local": '"{school_name}" "{location}" (alamat OR address)',
        
        # Team/Staff page search
        "team": '"{school_name}" (team OR staff OR "our team" OR "meet our" OR faculty OR teachers)',
        
        # Admissions search
        "admissions": '"{school_name}" (admissions OR pendaftaran OR enrollment) contact',
        
        # NEW: Instagram bio discovery for Linktree/WhatsApp links
        "instagram_bio": 'site:instagram.com "{school_name}"',
        
        # NEW: Job postings to find department heads
        "job_postings": '"{school_name}" (Loker OR "Lowongan Kerja" OR hiring OR career)',
        
        # NEW: Foundation registry for official Ketua Yayasan
        "foundation_registry": 'site:vervalyayasan.data.kemdikbud.go.id "{school_name}"',
    }
    
    # ===========================================
    # LMS/Tech Stack Indicators
    # ===========================================
    LMS_INDICATORS = {
        "canvas": ["canvas", "instructure.com", "canvas.instructure"],
        "moodle": ["moodle", "/moodle/", "moodle.org"],
        "google_classroom": ["classroom.google.com", "google classroom", "googleclassroom"],
        "schoology": ["schoology", "schoology.com"],
        "managebac": ["managebac", "managebac.com"],
        "seesaw": ["seesaw", "web.seesaw.me"],
        "edmodo": ["edmodo", "edmodo.com"],
        "blackboard": ["blackboard", "blackboard.com"],
        "powerschool": ["powerschool", "powerschool.com"],
    }
    
    # ===========================================
    # Priority Pages for Scraping
    # ===========================================
    PRIORITY_PAGES = [
        # Indonesian pages
        "tentang-kami",
        "tentang",
        "profil",
        "struktur-organisasi",
        "pengurus",
        "kontak",
        "hubungi-kami",
        "hubungi",
        "visi-misi",
        "yayasan",
        "foundation",
        
        # English pages
        "about",
        "about-us",
        "organization",
        "structure",
        "leadership",
        "board",
        "team",
        "contact",
        "contact-us",
        "profile",
    ]
    
    # ===========================================
    # Validation Settings
    # ===========================================
    VALIDATE_WHATSAPP = os.getenv("VALIDATE_WHATSAPP", "true").lower() == "true"
    VALIDATE_EMAIL = os.getenv("VALIDATE_EMAIL", "true").lower() == "true"
    USE_WHATSAPP_API = os.getenv("USE_WHATSAPP_API", "false").lower() == "true"  # For external API
    WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")  # If using Waapi/Twilio
    
    # ===========================================
    # Validation
    # ===========================================
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.SERPER_API_KEY:
            errors.append("SERPER_API_KEY is not set")
        
        if cls.LLM_PROVIDER == "openrouter" and not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is not set (required for OpenRouter)")
        
        if cls.LLM_PROVIDER == "claude" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set (required for Claude)")
        
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set (required for OpenAI)")
        
        return errors


# Create singleton instance
config = Config()

