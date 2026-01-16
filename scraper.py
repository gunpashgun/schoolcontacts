"""
Web scraper for Indonesia EdTech Lead Gen Engine
Uses Crawl4AI (optimized for LLM) with Playwright fallback
"""
import asyncio
import re
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
from config import config
from models import ScrapedPage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """
    Web scraper optimized for extracting school/foundation information
    
    Primary: Crawl4AI - provides LLM-optimized markdown output
    Fallback: Playwright - for JavaScript-heavy sites
    """
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.delay = config.SCRAPE_DELAY_SECONDS
        self._crawl4ai_available = self._check_crawl4ai()
    
    def _check_crawl4ai(self) -> bool:
        """Check if Crawl4AI is available"""
        try:
            from crawl4ai import AsyncWebCrawler
            return True
        except ImportError:
            logger.warning("Crawl4AI not installed. Using Playwright fallback.")
            return False
    
    async def scrape_page(self, url: str) -> ScrapedPage:
        """
        Scrape a single page, automatically choosing the best method
        """
        # Skip non-HTML files
        skip_extensions = ['.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.svg', 
                          '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.mp3', '.mp4']
        url_lower = url.lower()
        if any(url_lower.endswith(ext) for ext in skip_extensions):
            logger.debug(f"Skipping non-HTML file: {url}")
            return ScrapedPage(url=url, title="", html_content="", text_content="", success=False, error="Skipped non-HTML")
        
        if self._crawl4ai_available:
            return await self._scrape_with_crawl4ai(url)
        else:
            return await self._scrape_with_playwright(url)
    
    async def _scrape_with_crawl4ai(self, url: str) -> ScrapedPage:
        """Scrape using Crawl4AI for LLM-optimized output"""
        try:
            from crawl4ai import AsyncWebCrawler
            
            async with AsyncWebCrawler(
                headless=config.HEADLESS_BROWSER,
                verbose=False
            ) as crawler:
                result = await crawler.arun(
                    url=url,
                    bypass_cache=True,
                    word_count_threshold=10,
                )
                
                # Crawl4AI provides clean markdown output
                return ScrapedPage(
                    url=url,
                    title=result.metadata.get("title", "") if result.metadata else "",
                    html_content=result.html or "",
                    text_content=result.markdown or result.cleaned_html or "",
                    links=self._extract_links(result.html or "", url),
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Crawl4AI error for {url}: {e}")
            # Try Playwright as fallback
            return await self._scrape_with_playwright(url)
    
    async def _scrape_with_playwright(self, url: str) -> ScrapedPage:
        """Fallback scraper using Playwright for JS-heavy sites"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=config.HEADLESS_BROWSER)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(2000)  # Wait for dynamic content
                    
                    html = await page.content()
                    text = await page.evaluate("() => document.body.innerText")
                    title = await page.title()
                    
                    return ScrapedPage(
                        url=url,
                        title=title,
                        html_content=html,
                        text_content=text,
                        links=self._extract_links(html, url),
                        success=True
                    )
                finally:
                    await browser.close()
                
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return ScrapedPage(
                url=url,
                title="",
                html_content="",
                text_content="",
                success=False,
                error=str(e)
            )
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML"""
        links = []
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        
        base_domain = urlparse(base_url).netloc
        
        for match in href_pattern.finditer(html):
            href = match.group(1)
            
            # Skip anchors, javascript, mailto
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = urljoin(base_url, href)
            else:
                full_url = urljoin(base_url, href)
            
            # Only include same-domain links
            if urlparse(full_url).netloc == base_domain:
                links.append(full_url)
        
        return list(set(links))
    
    async def scrape_school_website(
        self, 
        base_url: str, 
        max_pages: int = None
    ) -> List[ScrapedPage]:
        """
        Scrape a school website, focusing on relevant pages
        
        Priority pages (scraped first):
        - About/Tentang pages
        - Organization structure
        - Contact pages
        - Foundation/Yayasan pages
        
        Args:
            base_url: Starting URL (usually homepage)
            max_pages: Maximum pages to scrape (default from config)
            
        Returns:
            List of ScrapedPage objects
        """
        if max_pages is None:
            max_pages = config.MAX_PAGES_PER_SCHOOL
        
        pages = []
        to_visit = [base_url]
        domain = urlparse(base_url).netloc
        
        # Reset visited URLs for this website
        self.visited_urls = set()
        
        while to_visit and len(pages) < max_pages:
            url = to_visit.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            # Only scrape same domain
            if urlparse(url).netloc != domain:
                continue
            
            logger.info(f"  📄 Scraping: {url}")
            page = await self.scrape_page(url)
            
            if page.success:
                pages.append(page)
                
                # Prioritize important pages
                priority_links = []
                other_links = []
                
                for link in page.links:
                    link_lower = link.lower()
                    if any(kw in link_lower for kw in config.PRIORITY_PAGES):
                        priority_links.append(link)
                    elif link not in self.visited_urls:
                        other_links.append(link)
                
                # Add priority links first
                for link in priority_links:
                    if link not in self.visited_urls and link not in to_visit:
                        to_visit.insert(0, link)
                
                # Add other links at the end
                for link in other_links:
                    if link not in self.visited_urls and link not in to_visit:
                        to_visit.append(link)
            
            # Rate limiting
            await asyncio.sleep(self.delay)
        
        logger.info(f"  ✓ Scraped {len(pages)} pages from {domain}")
        return pages
    
    # ===========================================
    # Contact Extraction Methods
    # ===========================================
    
    def extract_whatsapp_links(self, text: str) -> List[str]:
        """
        Extract WhatsApp numbers from text
        
        Looks for:
        - wa.me/62xxx links
        - api.whatsapp.com links
        - Indonesian phone numbers (08xxx, +62xxx)
        
        Returns normalized +62 format numbers
        """
        whatsapp_numbers = []
        
        # wa.me links (most reliable)
        wa_me_pattern = re.compile(r'wa\.me/(\d+)', re.IGNORECASE)
        for match in wa_me_pattern.finditer(text):
            num = match.group(1)
            if num.startswith('62'):
                whatsapp_numbers.append(f"+{num}")
            else:
                whatsapp_numbers.append(f"+62{num}")
        
        # api.whatsapp.com links
        api_pattern = re.compile(r'api\.whatsapp\.com/send\?phone=(\d+)', re.IGNORECASE)
        for match in api_pattern.finditer(text):
            num = match.group(1)
            if num.startswith('62'):
                whatsapp_numbers.append(f"+{num}")
            else:
                whatsapp_numbers.append(f"+62{num}")
        
        # Indonesian phone numbers that might be WhatsApp
        phone_pattern = re.compile(r'(?:WA|WhatsApp|Whatsapp)[:\s]*([+]?[\d\s\-()]+)', re.IGNORECASE)
        for match in phone_pattern.finditer(text):
            raw_num = re.sub(r'[^\d+]', '', match.group(1))
            normalized = self._normalize_indonesian_phone(raw_num)
            if normalized:
                whatsapp_numbers.append(normalized)
        
        return list(set(whatsapp_numbers))
    
    def extract_all_phone_numbers(self, text: str) -> List[str]:
        """Extract all Indonesian phone numbers from text"""
        phones = []
        
        # Pattern for Indonesian phone numbers
        patterns = [
            r'(\+62[\d\s\-]{8,15})',           # +62 format
            r'(62[\d\s\-]{8,15})',              # 62 format
            r'(08[\d\s\-]{8,13})',              # 08xx format
            r'(0\d{2,3}[\s\-]?\d{6,8})',        # Landline: 021-1234567
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                raw = match.group(1)
                normalized = self._normalize_indonesian_phone(raw)
                if normalized:
                    phones.append(normalized)
        
        return list(set(phones))
    
    def _normalize_indonesian_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to +62 format"""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        if len(cleaned) < 10:
            return None
        
        # Convert to +62 format
        if cleaned.startswith('08'):
            return '+62' + cleaned[1:]
        elif cleaned.startswith('62') and not cleaned.startswith('+'):
            return '+' + cleaned
        elif cleaned.startswith('+62'):
            return cleaned
        elif cleaned.startswith('0'):
            # Landline
            return '+62' + cleaned[1:]
        
        return None
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        # Comprehensive email pattern
        email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            re.IGNORECASE
        )
        
        emails = email_pattern.findall(text)
        
        # Filter out common false positives
        filtered = []
        skip_patterns = ['example.com', 'domain.com', 'email.com', 'test.com']
        
        for email in emails:
            email_lower = email.lower()
            if not any(skip in email_lower for skip in skip_patterns):
                filtered.append(email.lower())
        
        return list(set(filtered))
    
    def extract_social_media(self, html: str) -> dict:
        """Extract social media links from HTML"""
        social = {}
        
        # Instagram
        ig_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', html, re.IGNORECASE)
        if ig_match:
            social['instagram'] = f"@{ig_match.group(1)}"
        
        # Facebook
        fb_match = re.search(r'facebook\.com/([a-zA-Z0-9.]+)', html, re.IGNORECASE)
        if fb_match:
            social['facebook'] = f"https://facebook.com/{fb_match.group(1)}"
        
        # YouTube
        yt_match = re.search(r'youtube\.com/(?:c/|channel/|@)([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
        if yt_match:
            social['youtube'] = f"https://youtube.com/{yt_match.group(0)}"
        
        # LinkedIn (company page)
        li_match = re.search(r'linkedin\.com/(?:company|school)/([a-zA-Z0-9-]+)', html, re.IGNORECASE)
        if li_match:
            social['linkedin'] = f"https://linkedin.com/{li_match.group(0)}"
        
        return social
    
    def compile_scraped_content(self, pages: List[ScrapedPage]) -> str:
        """Compile all scraped pages into a single text for LLM processing"""
        parts = []
        
        for page in pages:
            if page.success and page.text_content:
                parts.append(f"\n\n=== PAGE: {page.url} ===")
                parts.append(f"Title: {page.title}")
                parts.append(page.text_content[:8000])  # Limit per page
        
        return "\n".join(parts)
    
    # ===========================================
    # NEW: Tech Stack Detection
    # ===========================================
    
    def detect_lms_stack(self, pages: List[ScrapedPage]) -> List[str]:
        """
        Detect LMS/EdTech platforms from scraped pages
        
        Checks for indicators of:
        - Canvas, Moodle, Google Classroom
        - Schoology, ManageBac, Seesaw
        - Blackboard, PowerSchool
        
        Returns list of detected LMS platforms
        """
        detected_lms = []
        
        for page in pages:
            if not page.success:
                continue
            
            content = (page.html_content + " " + page.text_content).lower()
            
            for lms_name, indicators in config.LMS_INDICATORS.items():
                if lms_name not in detected_lms:
                    for indicator in indicators:
                        if indicator.lower() in content:
                            detected_lms.append(lms_name)
                            logger.info(f"  🖥️ Detected LMS: {lms_name}")
                            break
        
        return detected_lms
    
    # ===========================================
    # NEW: Linktree/Bio Scraping
    # ===========================================
    
    async def scrape_linktree(self, linktree_url: str) -> dict:
        """
        Scrape Linktree/Bio.fm page for WhatsApp and contact links
        
        Returns dict with:
        - whatsapp_links: List of WhatsApp numbers found
        - contact_links: Dict of labeled links (e.g., "Principal" -> "wa.me/...")
        """
        result = {
            "whatsapp_links": [],
            "contact_links": {},
            "source_url": linktree_url
        }
        
        try:
            page = await self.scrape_page(linktree_url)
            
            if not page.success:
                return result
            
            # Extract WhatsApp links
            wa_links = self.extract_whatsapp_links(page.html_content + " " + page.text_content)
            result["whatsapp_links"] = wa_links
            
            # Try to find labeled links (e.g., "Contact Principal", "Admissions")
            # Pattern: look for text near wa.me links
            html = page.html_content
            
            # Find all link blocks with labels
            link_patterns = [
                r'(?:<[^>]*>)*\s*([^<>]{1,50})\s*(?:</[^>]*>)*\s*(?:<a[^>]*href=["\']([^"\']*wa\.me[^"\']*)["\'][^>]*>)',
                r'(?:<a[^>]*href=["\']([^"\']*wa\.me[^"\']*)["\'][^>]*>)\s*(?:<[^>]*>)*\s*([^<>]{1,50})',
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if len(match) == 2:
                        label, url = match if 'wa.me' in match[1] else (match[1], match[0])
                        label_clean = re.sub(r'\s+', ' ', label).strip()
                        
                        # Check for relevant labels
                        role_keywords = ['principal', 'kepala', 'director', 'direktur', 
                                       'admissions', 'admission', 'pendaftaran',
                                       'contact', 'kontak', 'hubungi']
                        
                        for keyword in role_keywords:
                            if keyword in label_clean.lower():
                                result["contact_links"][label_clean] = url
                                logger.info(f"  📱 Found labeled WhatsApp: {label_clean}")
                                break
            
            logger.info(f"  ✓ Scraped Linktree: {len(wa_links)} WhatsApp links found")
            
        except Exception as e:
            logger.error(f"Linktree scraping error for {linktree_url}: {e}")
        
        return result
    
    # ===========================================
    # NEW: PDF Text Extraction
    # ===========================================
    
    def find_pdf_links(self, pages: List[ScrapedPage]) -> List[str]:
        """Find PDF links that might contain organization structure"""
        pdf_links = []
        
        structure_keywords = [
            'struktur', 'organisasi', 'organization', 'structure',
            'pengurus', 'board', 'yayasan', 'foundation',
            'about', 'tentang', 'profil', 'profile'
        ]
        
        for page in pages:
            if not page.success:
                continue
            
            # Find all PDF links
            pdf_pattern = re.compile(r'href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE)
            
            for match in pdf_pattern.finditer(page.html_content):
                pdf_url = match.group(1)
                pdf_url_lower = pdf_url.lower()
                
                # Check if PDF is related to organization structure
                for keyword in structure_keywords:
                    if keyword in pdf_url_lower:
                        # Convert relative URL to absolute
                        if not pdf_url.startswith('http'):
                            base = urlparse(page.url)
                            pdf_url = f"{base.scheme}://{base.netloc}{pdf_url if pdf_url.startswith('/') else '/' + pdf_url}"
                        
                        pdf_links.append(pdf_url)
                        logger.info(f"  📄 Found structure PDF: {pdf_url}")
                        break
        
        return list(set(pdf_links))
    
    async def extract_pdf_text(self, pdf_url: str) -> str:
        """
        Download and extract text from a PDF file
        
        Uses PyMuPDF (fitz) for text extraction
        Returns extracted text or empty string on failure
        """
        try:
            import httpx
            import fitz  # PyMuPDF
            
            # Download PDF
            async with httpx.AsyncClient() as client:
                response = await client.get(pdf_url, timeout=30.0, follow_redirects=True)
                response.raise_for_status()
                pdf_bytes = response.content
            
            # Extract text using PyMuPDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []
            
            for page_num in range(min(pdf_document.page_count, 10)):  # Limit to first 10 pages
                page = pdf_document[page_num]
                text_parts.append(page.get_text())
            
            pdf_document.close()
            
            extracted_text = "\n".join(text_parts)
            logger.info(f"  ✓ Extracted {len(extracted_text)} chars from PDF")
            
            return extracted_text
            
        except ImportError:
            logger.warning("PyMuPDF (fitz) not installed. PDF extraction disabled.")
            return ""
        except Exception as e:
            logger.error(f"PDF extraction error for {pdf_url}: {e}")
            return ""
    
    # ===========================================
    # NEW: Google Maps Data Fetching
    # ===========================================
    
    async def fetch_google_maps_data(
        self, 
        school_name: str, 
        location: str,
        serper_api_key: str
    ) -> Optional[Dict]:
        """
        Fetch school data from Google Maps via Serper API
        
        Google Maps in Indonesia usually has the most up-to-date phone numbers
        
        Args:
            school_name: Name of the school
            location: City/region
            serper_api_key: Serper API key for authentication
            
        Returns:
            Dict with:
            {
                "phone": "+62xxx",
                "rating": 4.5,
                "user_ratings_total": 150,
                "address": "...",
                "website": "..."
            }
        """
        try:
            import httpx
            
            # Use Serper's Google Maps search
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/places",
                    headers={
                        "X-API-KEY": serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": f"{school_name} {location}",
                        "gl": "id",  # Indonesia
                        "hl": "id"   # Indonesian language
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse Google Maps results
                    if "places" in data and len(data["places"]) > 0:
                        place = data["places"][0]
                        return {
                            "phone": place.get("phone", ""),
                            "rating": place.get("rating", 0),
                            "user_ratings_total": place.get("user_ratings_total", 0),
                            "address": place.get("address", ""),
                            "website": place.get("website", ""),
                            "source": "google_maps"
                        }
                    
                    # Fallback: try organic results if places not available
                    if "organic" in data and len(data["organic"]) > 0:
                        # Look for Google Maps links
                        for result in data["organic"]:
                            if "google.com/maps" in result.get("link", ""):
                                return {
                                    "phone": "",  # Will need to scrape from page
                                    "rating": 0,
                                    "user_ratings_total": 0,
                                    "address": result.get("snippet", ""),
                                    "website": result.get("link", ""),
                                    "source": "google_maps"
                                }
        except Exception as e:
            logger.error(f"Google Maps fetch error: {e}")
        
        return None

