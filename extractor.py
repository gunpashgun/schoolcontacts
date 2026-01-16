"""
LLM-based data extraction using LangChain for Indonesia EdTech Lead Gen Engine
Supports Claude 3.5 Sonnet (recommended) and GPT-4o-mini
"""
import json
import re
from typing import List, Optional
from config import config
from models import DecisionMaker, SchoolData, RolePriority
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    Extract structured data from unstructured text using LLM
    
    Uses Indonesian-specific prompts optimized for:
    - Finding decision makers (Ketua Yayasan, Kepala Sekolah, etc.)
    - Extracting WhatsApp numbers (wa.me links, +62 format)
    - Identifying foundation/school hierarchy
    
    Supports: OpenRouter, Anthropic Claude, OpenAI
    """
    
    def __init__(self):
        self.llm = self._init_llm()
        self._extraction_count = 0
    
    def _init_llm(self):
        """Initialize the LLM based on configuration"""
        if config.LLM_PROVIDER == "openrouter":
            from langchain_openai import ChatOpenAI
            logger.info(f"Using OpenRouter with model: {config.OPENROUTER_MODEL}")
            return ChatOpenAI(
                model=config.OPENROUTER_MODEL,
                openai_api_key=config.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0,
                max_tokens=4096,
                default_headers={
                    "HTTP-Referer": "https://github.com/schoolcontacts",
                    "X-Title": "Indonesia EdTech Lead Gen"
                }
            )
        elif config.LLM_PROVIDER == "claude":
            from langchain_anthropic import ChatAnthropic
            logger.info("Using Claude 3.5 Sonnet for extraction")
            return ChatAnthropic(
                model=config.CLAUDE_MODEL,
                anthropic_api_key=config.ANTHROPIC_API_KEY,
                temperature=0,
                max_tokens=4096
            )
        else:
            from langchain_openai import ChatOpenAI
            logger.info("Using GPT-4o-mini for extraction")
            return ChatOpenAI(
                model=config.OPENAI_MODEL,
                openai_api_key=config.OPENAI_API_KEY,
                temperature=0,
                max_tokens=4096
            )
    
    async def extract_school_data(
        self, 
        school_name: str,
        school_type: str,
        location: str,
        scraped_content: str,
        search_results: str
    ) -> SchoolData:
        """
        Extract complete structured school data from raw content
        
        Args:
            school_name: Name of the school
            school_type: Type (Private Christian, International, etc.)
            location: City/region
            scraped_content: Text content from scraped pages
            search_results: Compiled search results text
            
        Returns:
            SchoolData object with extracted information
        """
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", self._get_extraction_prompt(
                school_name, school_type, location, 
                scraped_content, search_results
            ))
        ])
        
        try:
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            self._extraction_count += 1
            
            # Parse the JSON response
            content = response.content
            json_str = self._extract_json(content)
            
            if json_str:
                data = json.loads(json_str)
                
                # Fix type issues from LLM response
                if 'foundation_established' in data and data['foundation_established'] is not None:
                    data['foundation_established'] = str(data['foundation_established'])
                if 'npsn' in data and data['npsn'] is not None:
                    if isinstance(data['npsn'], list):
                        data['npsn'] = str(data['npsn'][0]) if data['npsn'] else None
                    else:
                        data['npsn'] = str(data['npsn'])
                
                # Convert decision_makers to proper objects
                if 'decision_makers' in data:
                    dms = []
                    for dm in data['decision_makers']:
                        # Assign priority based on role
                        priority = self._get_role_priority(
                            dm.get('role_indonesian', '') or dm.get('role', '')
                        )
                        dm['priority'] = priority.value
                        dms.append(DecisionMaker(**dm))
                    data['decision_makers'] = dms
                
                school_data = SchoolData(**data)
                school_data.calculate_quality_score()
                return school_data
            
            # If no JSON found, return basic structure
            logger.warning(f"Could not parse LLM response for {school_name}")
            return SchoolData(
                school_name=school_name,
                school_type=school_type,
                location=location
            )
            
        except Exception as e:
            logger.error(f"Extraction error for {school_name}: {e}")
            return SchoolData(
                school_name=school_name,
                school_type=school_type,
                location=location,
                processing_notes=f"Extraction error: {str(e)}"
            )
    
    def _get_system_prompt(self) -> str:
        """System prompt optimized for Indonesian education sector - PERSONA FOCUSED"""
        return """You are an expert data extraction assistant specializing in the Indonesian education sector.
Your task is to extract KEY STAKEHOLDERS as INDIVIDUAL PEOPLE (not general school contacts).

## CRITICAL: PRIORITIZE INDIVIDUAL PEOPLE OVER GENERAL CONTACTS

For each person, you MUST extract:
- Full Name (not abbreviations)
- Exact Title in Bahasa Indonesia (e.g., "Ketua Yayasan", "Kepala Sekolah")
- Their DIRECT contact (WhatsApp/Email tied to THEM specifically, not general school)
- LinkedIn URL if available
- Source URL where their name was found

## Key Stakeholder Hierarchy (STRICT PRIORITY ORDER)

### PRIORITY 1: Ketua Yayasan / Pembina (Owner/Chairman)
- The ULTIMATE decision maker for EdTech purchases
- Indonesian: Ketua Yayasan, Pendiri, Pembina, Ketua Pengurus, Dewan Pembina
- English: Chairman, Founder, Owner, Patron, Board Member

### PRIORITY 2: Direktur Pendidikan / Operational Director
- Daily operations and budget control
- Indonesian: Direktur, Direktur Pendidikan, Direktur Utama, Direktur Eksekutif
- English: Director, CEO, Managing Director, Executive Director

### PRIORITY 3: Kepala Sekolah (Principal)
- School-level decisions and implementation
- Indonesian: Kepala Sekolah, Kepala SD, Kepala SMP, Kepala SMA, Kepala TK
- English: Principal, Head of School, Headmaster, Headmistress

### PRIORITY 4: Operator Sekolah / Bendahara (School Operator/Treasurer) - NEW PRIORITY
- Operator Sekolah manages digital tools and EdTech systems (CRITICAL for EdTech)
- Bendahara controls budget for technology purchases
- Indonesian: Operator Sekolah, Bendahara, Pengelola Sistem
- English: School Operator, Treasurer, System Administrator
- Found in DAPODIK/government portals

### PRIORITY 5: Head of IT / Curriculum Coordinator
- CRITICAL for EdTech product decisions
- Indonesian: Koordinator Akademik, Koordinator Kurikulum, Kepala IT, Koordinator ICT
- English: Academic Coordinator, Curriculum Coordinator, IT Director, Technology Coordinator

### PRIORITY 6: Admissions & Marketing
- Key for B2B partnerships and demos
- Indonesian: Kepala Admisi, Manajer Admisi, Kepala Marketing, Humas
- English: Head of Admissions, Admissions Manager, Marketing Director

## Contact Format Rules for Indonesia

### WhatsApp Numbers (CRITICAL):
- Look for "Nomor HP" or "WA" or "WhatsApp" labels
- Indonesian mobile numbers: "08xxx" or "+62 8xxx" format
- Personal numbers start with 08 (mobile) or +62 8
- Extract from: wa.me/62xxx, api.whatsapp.com, or plain text "WA: 08xxx"
- Pattern: "Nomor HP: 08xxx" or "HP: 08xxx" or "WA: +62 8xxx"

### Email Classification:
- PERSONAL emails: name@school.sch.id, firstname.lastname@, personal patterns
- GENERAL emails: info@, admin@, contact@, kontak@, hubungi@ (flag as general)
- Mark email_is_personal: true for personal, false for general

### DAPODIK Data Priority:
- If you see DAPODIK/Government portal data, prioritize:
  1. Operator Sekolah (School Operator) - manages EdTech
  2. Bendahara (Treasurer) - budget decisions
  3. Kepala Sekolah (Principal) - official contact

## WhatsApp Priority

Indonesian business runs on WhatsApp. For each person, look for:
- wa.me/62xxx links associated with their name
- "Nomor HP: 08xxx" or "WA: 08xxx" or "WhatsApp: +62xxx" near their role
- Linktree/Bio links labeled with their role (e.g., "Contact Principal")

## Output Requirements

1. Extract MAXIMUM PEOPLE with roles (we need all contacts)
2. EACH person as separate entry (don't merge contacts)
3. Distinguish DIRECT contacts from GENERAL school contacts
4. Include source_url for EACH person (where you found them)
5. Rate confidence (0.0-1.0) based on how certain you are

Return ONLY valid JSON, no additional text."""

    def _get_extraction_prompt(
        self, 
        school_name: str, 
        school_type: str, 
        location: str,
        scraped_content: str,
        search_results: str
    ) -> str:
        """Build the extraction prompt with all available data"""
        
        # Truncate content to fit context window
        scraped_truncated = scraped_content[:12000] if scraped_content else "No content scraped"
        search_truncated = search_results[:6000] if search_results else "No search results"
        
        # Escape curly braces to prevent LangChain template interpretation
        scraped_truncated = scraped_truncated.replace("{", "{{").replace("}", "}}")
        search_truncated = search_truncated.replace("{", "{{").replace("}", "}}")
        
        # Build prompt without f-string curly braces issues
        prompt = """Extract all available information for this Indonesian school:

**School Name:** SCHOOL_NAME_PLACEHOLDER
**School Type:** SCHOOL_TYPE_PLACEHOLDER
**Location:** LOCATION_PLACEHOLDER

---

## SEARCH RESULTS

SEARCH_RESULTS_PLACEHOLDER

---

## SCRAPED WEBSITE CONTENT

SCRAPED_CONTENT_PLACEHOLDER

---

## EXTRACTION TASK

Extract and return a JSON object. The JSON must have these fields:
- school_name: the school name
- school_type: the school type
- location: the location
- npsn: 8-digit NPSN if found, null otherwise
- foundation_name: Name of Yayasan/Foundation if identified
- foundation_established: Year if mentioned
- decision_makers: array of objects with name, role, role_indonesian, email, phone, whatsapp, linkedin_url, source_url, confidence, email_is_personal (true if personal email, false if general like info@, admin@)
- official_website: main school website URL
- official_email: general contact email
- whatsapp_business: main WhatsApp for business inquiries
- phone_numbers: array of all phone numbers found
- instagram: handle or URL
- facebook: page URL
- source_urls: array of all URLs used as sources

## PERSONA-FOCUSED EXTRACTION RULES

1. **PRIORITIZE INDIVIDUAL PEOPLE** - We want named contacts, not "info@school.com"
2. **HIERARCHY MATTERS**:
   - Ketua Yayasan / Pembina (Owner/Chairman) - #1 TARGET
   - Direktur Pendidikan (Operational Director) - #2 TARGET
   - Kepala Sekolah (Principal) - #3 TARGET
   - Operator Sekolah / Bendahara - #4 TARGET (from DAPODIK - manages EdTech/budget)
   - Head of IT / Curriculum Coordinator - #5 TARGET (EdTech key person)
3. **DIRECT CONTACT per person** - Find WhatsApp/Email specific to each person's role
4. **Source tracking** - Note which URL each person was found on
5. **NO DUPLICATES** - Each person appears once with their most complete info

## Indonesian Contact Patterns

Look for these specific patterns:
- "Nomor HP: 08xxx" or "HP: 08xxx"
- "WA: 08xxx" or "WhatsApp: +62 8xxx"
- Personal emails: "nama@school.sch.id" (name-based) - mark email_is_personal: true
- General emails: "info@", "admin@", "kontak@" - mark email_is_personal: false

## DAPODIK Priority Roles

If extracting from DAPODIK/government pages:
1. Operator Sekolah (School Operator) - HIGH PRIORITY for EdTech
2. Bendahara (Treasurer) - Budget decisions
3. Kepala Sekolah (Principal) - Official contact

## What Makes a Good Lead

GOOD: "Budi Santoso, Ketua Yayasan, WhatsApp: +6281234567890, LinkedIn: linkedin.com/in/budi-santoso"
BAD: "Contact us at info@school.com" (no person identified)

GOOD: "Dr. Sarah Wong - Head of IT - sarah.wong@school.edu"  
BAD: "IT Department: it@school.com" (no person identified)

Extract as many NAMED individuals as possible. Return ONLY the JSON object."""

        # Replace placeholders
        prompt = prompt.replace("SCHOOL_NAME_PLACEHOLDER", school_name)
        prompt = prompt.replace("SCHOOL_TYPE_PLACEHOLDER", school_type)
        prompt = prompt.replace("LOCATION_PLACEHOLDER", location)
        prompt = prompt.replace("SEARCH_RESULTS_PLACEHOLDER", search_truncated)
        prompt = prompt.replace("SCRAPED_CONTENT_PLACEHOLDER", scraped_truncated)
        
        return prompt

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON object from LLM response"""
        # Try different patterns to find JSON
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'(\{[\s\S]*\})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Validate it's proper JSON
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
        
        # Try the whole text as JSON
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _get_role_priority(self, role: str) -> RolePriority:
        """Determine priority level based on role title"""
        role_lower = role.lower() if role else ""
        
        # Highest priority: Foundation leadership
        if any(kw in role_lower for kw in ['ketua yayasan', 'chairman', 'founder', 'pendiri']):
            return RolePriority.HIGHEST
        
        # High priority: Directors and Patrons
        if any(kw in role_lower for kw in ['pembina', 'patron', 'direktur', 'director']):
            return RolePriority.HIGH
        
        # Medium priority: Principals
        if any(kw in role_lower for kw in ['kepala sekolah', 'principal', 'head of school']):
            return RolePriority.MEDIUM
        
        # Low priority: Vice principals, Treasurers
        if any(kw in role_lower for kw in ['wakil', 'vice', 'bendahara', 'treasurer', 'sekretaris']):
            return RolePriority.LOW
        
        return RolePriority.LOWEST
    
    async def extract_decision_makers_quick(
        self, 
        text: str, 
        source_url: str
    ) -> List[DecisionMaker]:
        """
        Quick extraction of just decision makers from a single page
        Useful for targeted extraction from specific pages
        """
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting names and roles of school/foundation leadership from Indonesian text.
Look specifically for these roles:
- Ketua Yayasan (Foundation Chairman)
- Pembina (Patron)
- Kepala Sekolah (Principal)
- Direktur (Director)
- Bendahara (Treasurer)

Return a JSON array of decision makers found."""),
            ("human", f"""Extract all decision makers from this text:

{text[:6000]}

Source URL: {source_url}

Return JSON array:
[{{"name": "...", "role": "...", "role_indonesian": "...", "phone": "...", "whatsapp": "...", "email": "...", "source_url": "{source_url}", "confidence": 0.0-1.0}}]

Return ONLY the JSON array, no other text.""")
        ])
        
        try:
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            json_str = self._extract_json(response.content)
            if json_str:
                data = json.loads(json_str)
                if isinstance(data, list):
                    dms = []
                    for dm in data:
                        priority = self._get_role_priority(
                            dm.get('role_indonesian', '') or dm.get('role', '')
                        )
                        dm['priority'] = priority.value
                        dms.append(DecisionMaker(**dm))
                    return dms
            
        except Exception as e:
            logger.error(f"Quick extraction error: {e}")
        
        return []
    
    async def validate_and_deduplicate(
        self, 
        school_data: SchoolData
    ) -> SchoolData:
        """
        Post-process extracted data to validate and remove duplicates
        """
        # Deduplicate decision makers by name
        seen_names = set()
        unique_dms = []
        
        for dm in school_data.decision_makers:
            if dm.name:
                name_key = dm.name.lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_dms.append(dm)
        
        # Sort by priority
        unique_dms.sort(key=lambda x: list(RolePriority).index(x.priority))
        school_data.decision_makers = unique_dms
        
        # Deduplicate phone numbers
        school_data.phone_numbers = list(set(school_data.phone_numbers))
        
        # Deduplicate source URLs
        school_data.source_urls = list(set(school_data.source_urls))
        
        # Recalculate quality score
        school_data.calculate_quality_score()
        
        return school_data
    
    @property
    def extractions_made(self) -> int:
        """Get count of LLM extractions performed"""
        return self._extraction_count

