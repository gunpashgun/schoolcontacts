"""
School data definitions for Indonesia EdTech Lead Gen Engine
Contains all target schools organized by priority and location
"""
from models import SchoolInput
from typing import List


# ===========================================
# PRIORITY SCHOOLS - Surabaya (Week 1)
# ===========================================
PRIORITY_SCHOOLS: List[SchoolInput] = [
    SchoolInput(
        name="PPPK Petra",
        type="Private Christian",
        location="Surabaya",
        notes="Elementary to High School, Education Board/Group - Major Christian school network"
    ),
    SchoolInput(
        name="Yohanes Gabriel Foundation",
        type="Private Catholic",
        location="Surabaya",
        notes="Elementary to High School, Religious Foundation - Well-established Catholic school"
    ),
    SchoolInput(
        name="Santa Clara Catholic School",
        type="Private Catholic",
        location="Surabaya",
        notes="Elementary to Junior High, Religious Foundation"
    ),
    SchoolInput(
        name="Gloria Christian School",
        type="Private Christian",
        location="Surabaya",
        notes="Elementary to High School, Foundation"
    ),
    SchoolInput(
        name="Stella Maris School",
        type="Private Catholic",
        location="Surabaya",
        notes="Elementary to Junior High, Foundation - Part of larger Stella Maris network"
    ),
]


# ===========================================
# NATIONAL/GROUP SCHOOLS
# ===========================================
NATIONAL_GROUP_SCHOOLS: List[SchoolInput] = [
    # Lippo Group Schools
    SchoolInput(
        name="Sekolah Dian Harapan",
        type="Private Christian",
        location="Multiple cities",
        notes="Kindergarten to High School, Lippo/YPPH Group - Major education group"
    ),
    SchoolInput(
        name="Sekolah Pelita Harapan",
        type="Private International",
        location="Multiple cities",
        notes="Preschool to High School, Lippo/YPPH Group - Premium international school"
    ),
    
    # Major National Groups
    SchoolInput(
        name="BINUS School",
        type="Private International",
        location="Multiple cities",
        notes="Preschool to High School, BINUS Education Group"
    ),
    SchoolInput(
        name="BPK Penabur",
        type="Private Christian",
        location="Multiple cities",
        notes="Preschool to High School, National Christian Education Group"
    ),
    SchoolInput(
        name="Tarakanita",
        type="Private Catholic",
        location="Multiple cities",
        notes="Preschool to High School, National Catholic Education Group"
    ),
    SchoolInput(
        name="Al Azhar Islamic School",
        type="Private Islamic",
        location="Multiple cities",
        notes="Preschool to High School, National Islamic Education Group"
    ),
    SchoolInput(
        name="Singapore Intercultural School",
        type="International",
        location="Multiple cities",
        notes="Preschool to High School, SIS Global Group"
    ),
]


# ===========================================
# REGIONAL SCHOOLS
# ===========================================
REGIONAL_SCHOOLS: List[SchoolInput] = [
    # Surabaya/East Java
    SchoolInput(
        name="Sekolah Taman Mahatma Gandhi",
        type="Private National Plus",
        location="Surabaya",
        notes="Kindergarten to High School"
    ),
    SchoolInput(
        name="San Jose School",
        type="Private Catholic",
        location="Surabaya",
        notes="Kindergarten to High School"
    ),
    SchoolInput(
        name="Jembatan Bangsa School",
        type="Private National Plus",
        location="Surabaya",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Universal School",
        type="Private National Plus",
        location="Surabaya",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Albana Islamic School",
        type="Private Islamic",
        location="Surabaya",
        notes="Elementary to Junior High"
    ),
    SchoolInput(
        name="Anak Emas School",
        type="Private National Plus",
        location="Surabaya",
        notes="Preschool to Elementary"
    ),
    
    # Semarang/Central Java
    SchoolInput(
        name="Sekolah Nasima",
        type="Private Islamic",
        location="Semarang",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Semarang Multinational School",
        type="International",
        location="Semarang",
        notes="Preschool to High School, Independent Foundation"
    ),
    SchoolInput(
        name="Sekolah Nusaputera",
        type="Private National",
        location="Semarang",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Sekolah Islam Bina Amal",
        type="Private Islamic",
        location="Semarang",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Pangudi Luhur Bernadus",
        type="Private Catholic",
        location="Semarang",
        notes="Elementary to Junior High"
    ),
    SchoolInput(
        name="Sekolah Tunas Bangsa",
        type="Private Christian",
        location="Semarang",
        notes="Preschool to High School"
    ),
]


# ===========================================
# JAKARTA B2B TARGETS (Koding Next Poach)
# ===========================================
JAKARTA_B2B_TARGETS: List[SchoolInput] = [
    # International Schools
    SchoolInput(
        name="ACG School Jakarta",
        type="International",
        location="Jakarta",
        notes="Kindergarten to High School, Inspired Education Global Group"
    ),
    SchoolInput(
        name="Australian Independent School",
        type="International",
        location="Jakarta",
        notes="Preschool to High School, Independent Foundation"
    ),
    SchoolInput(
        name="Jakarta Intercultural School",
        type="International",
        location="Jakarta",
        notes="Preschool to High School, Premium International School - JIS"
    ),
    SchoolInput(
        name="Jakarta Multicultural School",
        type="International",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Independent School Jakarta",
        type="International",
        location="Jakarta",
        notes="Preschool to Junior High"
    ),
    SchoolInput(
        name="BTB School",
        type="International",
        location="Jakarta",
        notes="Preschool to High School, Bina Tunas Bangsa"
    ),
    SchoolInput(
        name="Bina Bangsa School",
        type="Private International",
        location="Jakarta",
        notes="Preschool to High School, BBS Group"
    ),
    
    # National Plus Schools
    SchoolInput(
        name="Sekolah Cikal",
        type="Private National Plus",
        location="Jakarta",
        notes="Preschool to High School, Education Group"
    ),
    SchoolInput(
        name="Sekolah Cita Buana",
        type="Private National Plus",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Global Prestasi School",
        type="Private",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Jakarta Bilingual Montessori School",
        type="Private",
        location="Jakarta",
        notes="Preschool to Junior High, JBMS"
    ),
    SchoolInput(
        name="Jakarta Nanyang School",
        type="Private Trilingual",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Sekolah Karakter",
        type="Private",
        location="Jakarta",
        notes="Preschool to High School, Character Education Focus"
    ),
    
    # Religious Schools
    SchoolInput(
        name="Al-Wildan Islamic School",
        type="Private Islamic",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Nizhamia Andalusia",
        type="Private Islamic",
        location="Jakarta",
        notes="Preschool & Elementary"
    ),
    SchoolInput(
        name="Marie Joseph School",
        type="Private Catholic",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Mawar Sharon Christian School",
        type="Private Christian",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Saint John's School",
        type="Private Catholic",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Sekolah Lentera Kasih",
        type="Private Christian",
        location="Jakarta",
        notes="Preschool to High School, SLK"
    ),
    SchoolInput(
        name="Tzu Chi School",
        type="Private Buddhist",
        location="Jakarta",
        notes="Preschool to High School, Buddhist Foundation"
    ),
    
    # Specialized/Other
    SchoolInput(
        name="All-Star Academy",
        type="Private/Hybrid",
        location="Jakarta",
        notes="Preschool to High School"
    ),
    SchoolInput(
        name="Julia Gabriel Centre",
        type="Enrichment/Preschool",
        location="Jakarta",
        notes="Early Learning, Franchise Group"
    ),
    SchoolInput(
        name="Playhouse Academy",
        type="Preschool",
        location="Jakarta",
        notes="Early Years"
    ),
    
    # Public Schools (for reference)
    SchoolInput(
        name="SMA Negeri 6 Jakarta",
        type="Public",
        location="Jakarta",
        notes="Senior High School, Government - Top public school"
    ),
    SchoolInput(
        name="SMA Negeri 70 Jakarta",
        type="Public",
        location="Jakarta",
        notes="Senior High School, Government - Top public school"
    ),
]


# ===========================================
# BALI SCHOOLS
# ===========================================
BALI_SCHOOLS: List[SchoolInput] = [
    SchoolInput(
        name="Pelangi School",
        type="Private",
        location="Bali",
        notes="Preschool to Junior High"
    ),
    SchoolInput(
        name="Taman Rama Intercultural School",
        type="Private",
        location="Bali",
        notes="Preschool to High School"
    ),
]


# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def get_priority_schools() -> List[SchoolInput]:
    """Get the 5 priority schools in Surabaya for Week 1"""
    return PRIORITY_SCHOOLS


def get_all_schools() -> List[SchoolInput]:
    """Get all schools in the database"""
    all_schools = []
    all_schools.extend(PRIORITY_SCHOOLS)
    all_schools.extend(NATIONAL_GROUP_SCHOOLS)
    all_schools.extend(REGIONAL_SCHOOLS)
    all_schools.extend(JAKARTA_B2B_TARGETS)
    all_schools.extend(BALI_SCHOOLS)
    return all_schools


def get_schools_by_location(location: str) -> List[SchoolInput]:
    """Filter schools by location (case-insensitive partial match)"""
    location_lower = location.lower()
    return [
        school for school in get_all_schools()
        if location_lower in school.location.lower()
    ]


def get_schools_by_type(school_type: str) -> List[SchoolInput]:
    """Filter schools by type (case-insensitive partial match)"""
    type_lower = school_type.lower()
    return [
        school for school in get_all_schools()
        if type_lower in school.type.lower()
    ]


def get_international_schools() -> List[SchoolInput]:
    """Get all international schools"""
    return [
        school for school in get_all_schools()
        if 'international' in school.type.lower()
    ]


def get_religious_schools(religion: str = None) -> List[SchoolInput]:
    """Get religious schools, optionally filtered by religion"""
    all_schools = get_all_schools()
    
    if religion:
        religion_lower = religion.lower()
        return [
            school for school in all_schools
            if religion_lower in school.type.lower()
        ]
    
    # All religious schools
    religious_keywords = ['christian', 'catholic', 'islamic', 'buddhist', 'muslim']
    return [
        school for school in all_schools
        if any(kw in school.type.lower() for kw in religious_keywords)
    ]


def get_schools_batch(batch_size: int = 5, offset: int = 0) -> List[SchoolInput]:
    """Get a batch of schools for processing (useful for rate limiting)"""
    all_schools = get_all_schools()
    return all_schools[offset:offset + batch_size]


def get_school_count() -> dict:
    """Get count of schools by category"""
    return {
        "priority_surabaya": len(PRIORITY_SCHOOLS),
        "national_groups": len(NATIONAL_GROUP_SCHOOLS),
        "regional": len(REGIONAL_SCHOOLS),
        "jakarta_b2b": len(JAKARTA_B2B_TARGETS),
        "bali": len(BALI_SCHOOLS),
        "total": len(get_all_schools())
    }


# ===========================================
# DISPLAY HELPERS
# ===========================================

def print_school_summary():
    """Print a summary of all schools in the database"""
    counts = get_school_count()
    
    print("\n" + "=" * 50)
    print("📚 SCHOOL DATABASE SUMMARY")
    print("=" * 50)
    print(f"  Priority (Surabaya Week 1): {counts['priority_surabaya']}")
    print(f"  National Groups:            {counts['national_groups']}")
    print(f"  Regional Schools:           {counts['regional']}")
    print(f"  Jakarta B2B Targets:        {counts['jakarta_b2b']}")
    print(f"  Bali Schools:               {counts['bali']}")
    print("-" * 50)
    print(f"  TOTAL:                      {counts['total']}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print_school_summary()

