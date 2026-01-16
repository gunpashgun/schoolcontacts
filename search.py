"""
Serper.dev Google Search API integration for Indonesia EdTech Lead Gen Engine
"""
import httpx
import asyncio
import re
from typing import List, Dict, Optional
from config import config
from models import SearchResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerperSearch:
    """
    Google Search using Serper.dev API
    
    Serper provides fast, affordable Google search results.
    Free tier: 2,500 searches
    """
    
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self):
        self.api_key = config.SERPER_API_KEY
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not set in environment. Get one at https://serper.dev")
        
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.rate_limiter = asyncio.Semaphore(config.REQUESTS_PER_MINUTE)
        self._request_count = 0
    
    async def search(
        self, 
        query: str, 
        num_results: int = 10, 
        gl: str = "id",      # Geo-location: Indonesia
        hl: str = "id"       # Language: Indonesian
    ) -> List[SearchResult]:
        """
        Perform a Google search via Serper API
        
        Args:
            query: Search query
            num_results: Number of results to return (max 100)
            gl: Geo-location code (id = Indonesia)
            hl: Host language (id = Indonesian)
            
        Returns:
            List of SearchResult objects
        """
        async with self.rate_limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.BASE_URL,
                        headers=self.headers,
                        json={
                            "q": query,
                            "num": num_results,
                            "gl": gl,
                            "hl": hl
                        },
                        timeout=config.REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    self._request_count += 1
                    
                    results = []
                    for idx, item in enumerate(data.get("organic", [])):
                        results.append(SearchResult(
                            query=query,
                            url=item.get("link", ""),
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                            position=idx + 1
                        ))
                    
                    logger.info(f"✓ Found {len(results)} results for: {query[:60]}...")
                    return results
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for '{query}': {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Search error for '{query}': {e}")
                return []
    
    async def search_dapodik(self, school_name: str, npsn: Optional[str] = None) -> List[SearchResult]:
        """
        Search DAPODIK portal for official school data
        
        DAPODIK contains:
        - Operator Sekolah (School Operator) - manages digital tools
        - Bendahara (Treasurer) - financial decision maker
        - Official contact information
        
        Args:
            school_name: Name of the school
            npsn: Optional NPSN code for direct lookup
            
        Returns:
            List of SearchResult objects from DAPODIK portal
        """
        queries = []
        
        if npsn:
            # Direct NPSN lookup
            queries.append(f'site:sekolah.data.kemdikbud.go.id/index.php/chome/profil/ {npsn}')
        
        # School name search
        queries.append(f'site:sekolah.data.kemdikbud.go.id "{school_name}" profil')
        queries.append(f'site:dapodik.kemdikbud.go.id "{school_name}"')
        
        all_results = []
        for query in queries:
            results = await self.search(query, num_results=5)
            all_results.extend(results)
            await asyncio.sleep(0.3)
        
        return all_results
    
    async def search_school(self, school_name: str, location: str = "", npsn: Optional[str] = None) -> Dict[str, List[SearchResult]]:
        """
        Perform all targeted searches for a school
        
        This executes multiple search queries optimized for finding:
        - Official school data (NPSN, Ministry records)
        - LinkedIn profiles of founders/directors
        - Contact information (WhatsApp, email)
        - Foundation/organization structure
        
        Args:
            school_name: Name of the school
            location: City/region (optional, improves accuracy)
            npsn: Optional NPSN code for DAPODIK lookup
            
        Returns:
            Dict with search categories as keys, SearchResult lists as values
        """
        results = {}
        
        # Build search queries from templates - EXPANDED for max contacts
        queries = {
            "official_data": config.SEARCH_TEMPLATES["official_data"].format(school_name=school_name),
            "npsn": config.SEARCH_TEMPLATES["npsn"].format(school_name=school_name),
            "founders_linkedin": config.SEARCH_TEMPLATES["founders_linkedin"].format(school_name=school_name),
            "staff_linkedin": config.SEARCH_TEMPLATES["staff_linkedin"].format(school_name=school_name),
            "contacts": config.SEARCH_TEMPLATES["contacts"].format(school_name=school_name),
            "foundation": config.SEARCH_TEMPLATES["foundation"].format(school_name=school_name),
            "website": config.SEARCH_TEMPLATES["website"].format(school_name=school_name),
            "team": config.SEARCH_TEMPLATES["team"].format(school_name=school_name),
            "admissions": config.SEARCH_TEMPLATES["admissions"].format(school_name=school_name),
            # NEW: Enhanced search queries
            "instagram_bio": config.SEARCH_TEMPLATES["instagram_bio"].format(school_name=school_name),
            "job_postings": config.SEARCH_TEMPLATES["job_postings"].format(school_name=school_name),
            "foundation_registry": config.SEARCH_TEMPLATES["foundation_registry"].format(school_name=school_name),
        }
        
        # Add location-specific search if provided
        if location:
            queries["local"] = config.SEARCH_TEMPLATES["local"].format(
                school_name=school_name, 
                location=location
            )
        
        # Execute searches with small delays to be respectful
        for key, query in queries.items():
            results[key] = await self.search(query)
            await asyncio.sleep(0.3)  # Small delay between queries
        
        # NEW: DAPODIK search
        results["dapodik"] = await self.search_dapodik(school_name, npsn)
        
        return results
    
    def compile_results_text(self, results: Dict[str, List[SearchResult]]) -> str:
        """Compile all search results into a single text for LLM processing"""
        text_parts = []
        
        for category, items in results.items():
            if items:
                text_parts.append(f"\n=== {category.upper().replace('_', ' ')} ===")
                for item in items:
                    text_parts.append(f"Title: {item.title}")
                    text_parts.append(f"URL: {item.url}")
                    text_parts.append(f"Snippet: {item.snippet}")
                    text_parts.append("")
        
        return "\n".join(text_parts)
    
    def find_official_website(self, results: Dict[str, List[SearchResult]]) -> Optional[str]:
        """
        Find the most likely official school website from search results
        
        Priority order:
        1. .sch.id domains (Indonesian school domain)
        2. .ac.id domains (Indonesian academic domain)
        3. First non-social-media result
        """
        all_urls = []
        
        # Collect all URLs, prioritizing contacts and website searches
        for key in ["website", "contacts", "local", "foundation"]:
            items = results.get(key, [])
            for item in items:
                all_urls.append(item.url)
        
        # Social media and directory domains to skip
        skip_domains = [
            'linkedin.com', 'facebook.com', 'instagram.com', 
            'twitter.com', 'youtube.com', 'tiktok.com',
            'kemdikbud.go.id',  # Ministry site, not school site
            'wikipedia.org',
            'tripadvisor',
            'google.com',
        ]
        
        # First pass: look for .sch.id or .ac.id
        for url in all_urls:
            url_lower = url.lower()
            if any(skip in url_lower for skip in skip_domains):
                continue
            if '.sch.id' in url_lower or '.ac.id' in url_lower:
                return url
        
        # Second pass: any non-social URL
        for url in all_urls:
            url_lower = url.lower()
            if not any(skip in url_lower for skip in skip_domains):
                return url
        
        return None
    
    def find_linkedin_profiles(self, results: Dict[str, List[SearchResult]]) -> List[SearchResult]:
        """Extract LinkedIn profile results"""
        linkedin_results = []
        
        for key, items in results.items():
            for item in items:
                if 'linkedin.com/in/' in item.url.lower():
                    linkedin_results.append(item)
        
        return linkedin_results
    
    def find_linktree_urls(self, results: Dict[str, List[SearchResult]]) -> List[str]:
        """Extract Linktree/Bio.fm URLs from Instagram search results"""
        linktree_urls = []
        bio_patterns = [
            'linktr.ee', 'bio.fm', 'beacons.ai', 'linkin.bio',
            'campsite.bio', 'lnk.to', 'msha.ke', 'tap.bio'
        ]
        
        for key, items in results.items():
            for item in items:
                # Check snippet for bio link URLs
                for pattern in bio_patterns:
                    if pattern in item.snippet.lower():
                        # Try to extract full URL from snippet
                        import re
                        url_match = re.search(rf'(https?://)?{pattern}/[\w.-]+', item.snippet, re.IGNORECASE)
                        if url_match:
                            url = url_match.group(0)
                            if not url.startswith('http'):
                                url = 'https://' + url
                            linktree_urls.append(url)
        
        return list(set(linktree_urls))
    
    def find_instagram_profiles(self, results: Dict[str, List[SearchResult]]) -> List[str]:
        """Extract Instagram profile URLs"""
        instagram_urls = []
        
        for key, items in results.items():
            for item in items:
                if 'instagram.com/' in item.url.lower():
                    instagram_urls.append(item.url)
        
        return list(set(instagram_urls))
    
    @property
    def requests_made(self) -> int:
        """Get count of API requests made"""
        return self._request_count


class NPSNLookup:
    """
    Direct lookup from Indonesian Ministry of Education database
    
    NPSN (Nomor Pokok Sekolah Nasional) is an 8-digit unique identifier
    for every school in Indonesia. With this ID, we can get official data.
    """
    
    # Note: These are example URLs. The actual API may require different endpoints.
    KEMDIKBUD_SEARCH = "https://referensi.data.kemdikbud.go.id/pendidikan/dikdas"
    
    def extract_npsn_from_text(self, text: str) -> Optional[str]:
        """
        Extract NPSN code from text
        
        NPSN is always 8 digits, typically starting with province code:
        - 20xxxxxx: Java
        - 10xxxxxx: Sumatra
        - 30xxxxxx: Kalimantan
        - etc.
        """
        # Look for explicit NPSN labels
        npsn_patterns = [
            r'NPSN\s*[:\s]\s*(\d{8})',
            r'Nomor\s+Pokok\s+Sekolah\s*[:\s]\s*(\d{8})',
            r'\b(\d{8})\b(?=\s*(?:NPSN|npsn))',
        ]
        
        for pattern in npsn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: Look for any 8-digit number that could be NPSN
        # (less reliable, but useful as backup)
        eight_digit = re.findall(r'\b(\d{8})\b', text)
        for num in eight_digit:
            # NPSN typically starts with 1, 2, or 3 (Indonesian regions)
            if num[0] in '123':
                return num
        
        return None
    
    async def lookup_by_npsn(self, npsn: str) -> Optional[Dict]:
        """
        Get school details from Kemdikbud by NPSN
        
        Note: This method attempts to get data from the official registry.
        The actual implementation may need adjustment based on the API availability.
        """
        if not npsn or len(npsn) != 8:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Try the referensi data API
                response = await client.get(
                    f"https://referensi.data.kemdikbud.go.id/pendidikan/dikdas/detail/{npsn}",
                    timeout=15.0,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    # Parse the HTML response for school data
                    # This is a simplified example
                    return {
                        "npsn": npsn,
                        "html_content": response.text
                    }
                    
        except Exception as e:
            logger.debug(f"NPSN lookup failed for {npsn}: {e}")
        
        return None
    
    def parse_kemdikbud_data(self, html: str) -> Dict:
        """Parse school data from Kemdikbud HTML page"""
        data = {}
        
        # Extract principal name
        principal_match = re.search(
            r'Kepala\s+Sekolah\s*[:\s]+([^<\n]+)', 
            html, 
            re.IGNORECASE
        )
        if principal_match:
            data['principal_name'] = principal_match.group(1).strip()
        
        # Extract address
        address_match = re.search(
            r'Alamat\s*[:\s]+([^<\n]+)', 
            html, 
            re.IGNORECASE
        )
        if address_match:
            data['address'] = address_match.group(1).strip()
        
        # Extract email
        email_match = re.search(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', 
            html
        )
        if email_match:
            data['email'] = email_match.group(0)
        
        return data

