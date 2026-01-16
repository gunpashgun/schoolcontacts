#!/usr/bin/env python3
"""
Indonesia EdTech Lead Gen Engine
Main orchestrator for the lead enrichment pipeline

Usage:
    python main.py                     # Process priority schools (Surabaya)
    python main.py --all               # Process all schools
    python main.py --batch 5           # Process in batches of 5
    python main.py --location Jakarta  # Process Jakarta schools only
    python main.py --school "PPPK Petra"  # Process single school
"""

import asyncio
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from config import config, Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from models import (
    SchoolInput, SchoolData, DecisionMaker, ProcessingResult, 
    ProcessingStatus, BatchResult, PersonLead, FoundationCluster
)
from search import SerperSearch, NPSNLookup
from scraper import WebScraper
from extractor import LLMExtractor
from validator import validator
from schools_data import (
    get_priority_schools, 
    get_all_schools, 
    get_schools_by_location,
    get_school_count,
    print_school_summary
)

# Rich console for beautiful output
console = Console()


class LeadEnrichmentEngine:
    """
    Main orchestrator for the Indonesia EdTech Lead Gen Engine
    
    Pipeline:
    1. Search Phase - Find information using Serper (Google)
    2. Scraping Phase - Extract content from school websites
    3. AI Extraction Phase - Use LLM to parse and structure data
    4. Deduplication - Clean and validate results
    5. Export - Generate CSV/Excel output
    """
    
    def __init__(self):
        self.search = SerperSearch()
        self.scraper = WebScraper()
        self.extractor = LLMExtractor()
        self.npsn_lookup = NPSNLookup()
        
        # Ensure output directory exists
        config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    async def enrich_school(self, school: SchoolInput) -> ProcessingResult:
        """
        Full enrichment pipeline for a single school
        
        Returns ProcessingResult with status and data
        """
        start_time = time.time()
        result = ProcessingResult(
            school_input=school,
            status=ProcessingStatus.SEARCHING
        )
        
        try:
            console.print(f"\n🏫 [bold blue]Processing:[/bold blue] {school.name}")
            
            # ===========================================
            # PHASE 1: Search
            # ===========================================
            console.print("  🔍 Searching Google...")
            result.status = ProcessingStatus.SEARCHING
            
            # Extract NPSN early if available for DAPODIK search
            npsn_early = self.npsn_lookup.extract_npsn_from_text(
                f"{school.name} {school.location}"
            )
            
            search_results = await self.search.search_school(
                school.name, 
                school.location,
                npsn=npsn_early
            )
            
            result.search_results_count = sum(len(r) for r in search_results.values())
            search_text = self.search.compile_results_text(search_results)
            
            # Find official website and NPSN from search results
            official_url = self.search.find_official_website(search_results)
            npsn = self.npsn_lookup.extract_npsn_from_text(search_text)
            
            if official_url:
                console.print(f"  🌐 Found website: {official_url}")
            if npsn:
                console.print(f"  🆔 Found NPSN: {npsn}")
            
            # NEW: Fetch Google Maps data for up-to-date phone numbers
            google_maps_data = None
            if config.SERPER_API_KEY:
                try:
                    google_maps_data = await self.scraper.fetch_google_maps_data(
                        school.name,
                        school.location,
                        config.SERPER_API_KEY
                    )
                    if google_maps_data and google_maps_data.get("phone"):
                        console.print(f"  📍 Google Maps phone: {google_maps_data['phone']}")
                except Exception as e:
                    logger.debug(f"Google Maps fetch failed: {e}")
            
            # ===========================================
            # PHASE 2: Scraping
            # ===========================================
            scraped_content = ""
            source_urls = []
            whatsapp_numbers = []
            emails = []
            social_media = {}
            
            # NEW: Find Linktree/Bio URLs from search results
            linktree_urls = self.search.find_linktree_urls(search_results)
            linktree_whatsapp = {}
            
            if linktree_urls:
                console.print(f"  🔗 Found {len(linktree_urls)} Linktree/Bio URLs")
                for lt_url in linktree_urls[:2]:  # Limit to 2
                    lt_result = await self.scraper.scrape_linktree(lt_url)
                    whatsapp_numbers.extend(lt_result.get("whatsapp_links", []))
                    linktree_whatsapp.update(lt_result.get("contact_links", {}))
            
            # NEW: Tech stack detection
            tech_stack = []
            
            if official_url:
                console.print("  📄 Scraping website...")
                result.status = ProcessingStatus.SCRAPING
                
                pages = await self.scraper.scrape_school_website(official_url)
                result.pages_scraped = len(pages)
                
                # NEW: Detect LMS/EdTech platforms
                tech_stack = self.scraper.detect_lms_stack(pages)
                if tech_stack:
                    console.print(f"  🖥️ Detected tech stack: {', '.join(tech_stack)}")
                
                # NEW: Find and extract structure PDFs
                pdf_links = self.scraper.find_pdf_links(pages)
                for pdf_url in pdf_links[:2]:  # Limit to 2 PDFs
                    pdf_text = await self.scraper.extract_pdf_text(pdf_url)
                    if pdf_text:
                        scraped_content += f"\n\n=== PDF: {pdf_url} ===\n{pdf_text}"
                
                for page in pages:
                    if page.success:
                        scraped_content += f"\n\n=== {page.url} ===\n{page.text_content}"
                        source_urls.append(page.url)
                        
                        # Direct extraction of contacts from scraped content
                        whatsapp_numbers.extend(
                            self.scraper.extract_whatsapp_links(page.text_content + page.html_content)
                        )
                        emails.extend(self.scraper.extract_emails(page.text_content))
                        
                        # Extract social media
                        page_social = self.scraper.extract_social_media(page.html_content)
                        social_media.update(page_social)
            
            # ===========================================
            # PHASE 3: AI Extraction
            # ===========================================
            console.print("  🤖 Extracting with AI...")
            result.status = ProcessingStatus.EXTRACTING
            
            school_data = await self.extractor.extract_school_data(
                school_name=school.name,
                school_type=school.type,
                location=school.location,
                scraped_content=scraped_content,
                search_results=search_text
            )
            
            # ===========================================
            # PHASE 4: Merge & Deduplicate
            # ===========================================
            
            # Add NPSN if found
            if npsn and not school_data.npsn:
                school_data.npsn = npsn
            
            # Add official website
            if official_url and not school_data.official_website:
                school_data.official_website = official_url
            
            # Merge WhatsApp numbers
            all_whatsapp = set(whatsapp_numbers)
            if school_data.whatsapp_business:
                all_whatsapp.add(school_data.whatsapp_business)
            for dm in school_data.decision_makers:
                if dm.whatsapp:
                    all_whatsapp.add(dm.whatsapp)
            
            # Set primary WhatsApp
            if all_whatsapp and not school_data.whatsapp_business:
                school_data.whatsapp_business = list(all_whatsapp)[0]
            
            # Merge emails
            all_emails = set(emails)
            if school_data.official_email:
                all_emails.add(school_data.official_email)
            if all_emails and not school_data.official_email:
                school_data.official_email = list(all_emails)[0]
            
            # Add social media
            if not school_data.instagram and social_media.get('instagram'):
                school_data.instagram = social_media['instagram']
            if not school_data.facebook and social_media.get('facebook'):
                school_data.facebook = social_media['facebook']
            
            # NEW: Add tech stack
            if tech_stack:
                school_data.tech_stack = tech_stack
            
            # Add source URLs
            school_data.source_urls = list(set(source_urls))
            school_data.last_updated = datetime.now().isoformat()
            
            # NEW: Add Google Maps phone if found
            if google_maps_data and google_maps_data.get("phone"):
                if not school_data.whatsapp_business:
                    school_data.whatsapp_business = google_maps_data["phone"]
                elif google_maps_data["phone"] not in school_data.phone_numbers:
                    school_data.phone_numbers.append(google_maps_data["phone"])
            
            # Validate and deduplicate
            school_data = await self.extractor.validate_and_deduplicate(school_data)
            
            # ===========================================
            # PHASE 3.5: Contact Validation
            # ===========================================
            if config.VALIDATE_WHATSAPP or config.VALIDATE_EMAIL:
                console.print("  ✓ Validating contacts...")
                
                # Validate decision makers
                for dm in school_data.decision_makers:
                    if config.VALIDATE_WHATSAPP and dm.whatsapp:
                        wa_result = await validator.verify_whatsapp(
                            dm.whatsapp,
                            use_api=config.USE_WHATSAPP_API
                        )
                        dm.whatsapp_verified = wa_result.get("exists", False)
                    
                    if config.VALIDATE_EMAIL and dm.email:
                        email_result = await validator.verify_email_live(dm.email)
                        dm.email_verified = email_result.get("is_live", False)
                        dm.email_is_personal = email_result.get("is_personal", False)
                
                # Validate school-level WhatsApp
                if config.VALIDATE_WHATSAPP and school_data.whatsapp_business:
                    wa_result = await validator.verify_whatsapp(
                        school_data.whatsapp_business,
                        use_api=config.USE_WHATSAPP_API
                    )
                    # Could store in a new field if needed
                
                # Validate school-level email
                if config.VALIDATE_EMAIL and school_data.official_email:
                    email_result = await validator.verify_email_live(school_data.official_email)
                    # Could store in a new field if needed
                
                # Recalculate quality score with verification bonus
                school_data.calculate_quality_score()
            
            # ===========================================
            # Complete
            # ===========================================
            result.school_data = school_data
            result.status = ProcessingStatus.COMPLETED
            result.processing_time_seconds = time.time() - start_time
            
            # Log summary
            dm_count = len(school_data.decision_makers)
            has_wa = "✓" if school_data.whatsapp_business else "✗"
            has_email = "✓" if school_data.official_email else "✗"
            quality = f"{school_data.data_quality_score:.0%}"
            
            console.print(
                f"  ✅ [green]Complete[/green] | "
                f"DMs: {dm_count} | WA: {has_wa} | Email: {has_email} | "
                f"Quality: {quality} | Time: {result.processing_time_seconds:.1f}s"
            )
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.processing_time_seconds = time.time() - start_time
            console.print(f"  ❌ [red]Error:[/red] {e}")
        
        return result
    
    async def enrich_batch(
        self, 
        schools: List[SchoolInput],
        delay_between_schools: float = None
    ) -> BatchResult:
        """
        Process a batch of schools with progress tracking
        """
        if delay_between_schools is None:
            delay_between_schools = config.SCHOOL_DELAY_SECONDS
        
        batch_result = BatchResult(
            total_schools=len(schools),
            successful=0,
            failed=0,
            results=[],
            started_at=datetime.now().isoformat()
        )
        
        start_time = time.time()
        
        console.print(Panel.fit(
            f"[bold]Processing {len(schools)} schools[/bold]\n"
            f"Delay between schools: {delay_between_schools}s",
            title="🇮🇩 Indonesia EdTech Lead Gen Engine"
        ))
        
        for i, school in enumerate(schools, 1):
            console.print(f"\n📊 [bold]Progress:[/bold] {i}/{len(schools)}")
            
            result = await self.enrich_school(school)
            batch_result.results.append(result)
            
            if result.status == ProcessingStatus.COMPLETED:
                batch_result.successful += 1
            else:
                batch_result.failed += 1
            
            # Delay between schools (except for last one)
            if i < len(schools):
                await asyncio.sleep(delay_between_schools)
        
        batch_result.completed_at = datetime.now().isoformat()
        batch_result.total_time_seconds = time.time() - start_time
        
        return batch_result
    
    def export_to_csv(
        self, 
        results: List[ProcessingResult], 
        filename: str = None
    ) -> str:
        """Export results to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"leads_{timestamp}.csv"
        
        filepath = config.OUTPUT_DIR / filename
        rows = self._prepare_export_rows(results)
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        console.print(f"💾 [green]Exported to:[/green] {filepath}")
        return str(filepath)
    
    def export_to_excel(
        self, 
        results: List[ProcessingResult], 
        filename: str = None
    ) -> str:
        """Export results to Excel file with formatting"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"leads_{timestamp}.xlsx"
        
        filepath = config.OUTPUT_DIR / filename
        rows = self._prepare_export_rows(results)
        
        df = pd.DataFrame(rows)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Leads', index=False)
            
            # Auto-adjust column widths using openpyxl utility
            from openpyxl.utils import get_column_letter
            worksheet = writer.sheets['Leads']
            for idx, col in enumerate(df.columns, 1):  # 1-indexed for openpyxl
                max_len = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                col_letter = get_column_letter(idx)
                worksheet.column_dimensions[col_letter].width = min(max_len, 50)
        
        console.print(f"💾 [green]Exported to:[/green] {filepath}")
        return str(filepath)
    
    def _prepare_export_rows(self, results: List[ProcessingResult]) -> List[dict]:
        """Prepare rows for export"""
        rows = []
        
        for result in results:
            if result.school_data:
                data = result.school_data
                row = {
                    "School Name": data.school_name,
                    "School Type": data.school_type,
                    "Location": data.location,
                    "Foundation Name": data.foundation_name or "",
                    "NPSN": data.npsn or "",
                    "Official Website": data.official_website or "",
                    "Official Email": data.official_email or "",
                    "WhatsApp Business": data.whatsapp_business or "",
                    "Phone Numbers": ", ".join(data.phone_numbers) if data.phone_numbers else "",
                    "Instagram": data.instagram or "",
                    "Facebook": data.facebook or "",
                }
                
                # Add up to 8 decision makers for maximum contacts
                for i, dm in enumerate(data.decision_makers[:8], 1):
                    row[f"DM{i} Name"] = dm.name or ""
                    row[f"DM{i} Role"] = dm.role_indonesian or dm.role or ""
                    row[f"DM{i} LinkedIn"] = dm.linkedin_url or ""
                    row[f"DM{i} WhatsApp"] = dm.whatsapp or ""
                    row[f"DM{i} WA Verified"] = "✓" if dm.whatsapp_verified else ""
                    row[f"DM{i} Email"] = dm.email or ""
                    row[f"DM{i} Email Verified"] = "✓" if dm.email_verified else ""
                    row[f"DM{i} Email Type"] = "Personal" if dm.email_is_personal else "General"
                    row[f"DM{i} Phone"] = dm.phone or ""
                
                # Fill empty DM slots
                for i in range(len(data.decision_makers) + 1, 9):
                    row[f"DM{i} Name"] = ""
                    row[f"DM{i} Role"] = ""
                    row[f"DM{i} LinkedIn"] = ""
                    row[f"DM{i} WhatsApp"] = ""
                    row[f"DM{i} WA Verified"] = ""
                    row[f"DM{i} Email"] = ""
                    row[f"DM{i} Email Verified"] = ""
                    row[f"DM{i} Email Type"] = ""
                    row[f"DM{i} Phone"] = ""
                
                # Add verification status summary
                verified_wa = sum(1 for dm in data.decision_makers if dm.whatsapp_verified)
                verified_email = sum(1 for dm in data.decision_makers if dm.email_verified)
                row["Verified Contacts"] = f"WA: {verified_wa}, Email: {verified_email}"
                row["Status"] = self._get_verification_status(data)
                
                row["Data Quality"] = f"{data.data_quality_score:.0%}"
                row["Sources"] = ", ".join(data.source_urls[:3]) if data.source_urls else ""
                row["Last Updated"] = data.last_updated or ""
                row["Processing Status"] = result.status.value
                
            else:
                # Failed processing
                row = {
                    "School Name": result.school_input.name,
                    "School Type": result.school_input.type,
                    "Location": result.school_input.location,
                    "Status": "Guess",
                    "Processing Status": result.status.value,
                    "Error": result.error_message or "",
                }
            
            rows.append(row)
        
        return rows
    
    def _get_verification_status(self, data: SchoolData) -> str:
        """Get verification status string"""
        statuses = []
        
        for dm in data.decision_makers:
            if dm.whatsapp_verified and dm.email_verified:
                statuses.append("Verified WA + Email")
            elif dm.whatsapp_verified:
                statuses.append("Verified WA")
            elif dm.email_verified:
                statuses.append("Valid Email")
        
        if not statuses:
            return "Guess"
        
        return " / ".join(set(statuses))
    
    # ===========================================
    # NEW: Person-Centric Export
    # ===========================================
    
    def export_person_leads(
        self, 
        results: List[ProcessingResult], 
        filename: str = None
    ) -> str:
        """
        Export person-centric leads (one row per person)
        
        This is the new output format optimized for B2B outreach
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"person_leads_{timestamp}.csv"
        
        filepath = config.OUTPUT_DIR / filename
        person_leads = []
        
        for result in results:
            if result.school_data:
                for dm in result.school_data.decision_makers:
                    if dm.name:  # Only include named people
                        lead = PersonLead.from_decision_maker(dm, result.school_data)
                        person_leads.append(lead.to_dict())
        
        df = pd.DataFrame(person_leads)
        
        # Sort by Priority Tier (1 = highest priority)
        if not df.empty:
            df = df.sort_values(['Priority Tier', 'School Name'])
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        console.print(f"💾 [green]Person leads exported to:[/green] {filepath}")
        console.print(f"   Total people: {len(person_leads)}")
        
        return str(filepath)
    
    def export_person_leads_json(
        self, 
        results: List[ProcessingResult], 
        filename: str = None
    ) -> str:
        """Export person leads as JSON"""
        import json
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"person_leads_{timestamp}.json"
        
        filepath = config.OUTPUT_DIR / filename
        person_leads = []
        
        for result in results:
            if result.school_data:
                for dm in result.school_data.decision_makers:
                    if dm.name:
                        lead = PersonLead.from_decision_maker(dm, result.school_data)
                        person_leads.append(lead.to_dict())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(person_leads, f, ensure_ascii=False, indent=2)
        
        console.print(f"💾 [green]Person leads JSON exported to:[/green] {filepath}")
        return str(filepath)
    
    # ===========================================
    # NEW: Foundation Clustering
    # ===========================================
    
    def cluster_by_foundation(
        self, 
        results: List[ProcessingResult]
    ) -> List[FoundationCluster]:
        """
        Group schools by their foundation/Yayasan
        
        This helps identify opportunities where one contact 
        can open doors to multiple schools
        """
        from collections import defaultdict
        
        # Group schools by foundation name
        foundation_schools = defaultdict(list)
        foundation_data = defaultdict(lambda: {
            "schools": [],
            "contacts": [],
            "tech_stacks": set(),
            "has_whatsapp": False,
            "has_linkedin": False,
        })
        
        for result in results:
            if result.school_data:
                data = result.school_data
                foundation_name = data.foundation_name or "Unknown Foundation"
                
                foundation_data[foundation_name]["schools"].append(data.school_name)
                
                # Aggregate contacts
                for dm in data.decision_makers:
                    if dm.name:
                        lead = PersonLead.from_decision_maker(dm, data)
                        foundation_data[foundation_name]["contacts"].append(lead)
                        
                        if dm.whatsapp:
                            foundation_data[foundation_name]["has_whatsapp"] = True
                        if dm.linkedin_url:
                            foundation_data[foundation_name]["has_linkedin"] = True
                
                # Aggregate tech stacks
                for tech in data.tech_stack:
                    foundation_data[foundation_name]["tech_stacks"].add(tech)
        
        # Create FoundationCluster objects
        clusters = []
        for foundation_name, data in foundation_data.items():
            cluster = FoundationCluster(
                foundation_name=foundation_name,
                schools=data["schools"],
                total_schools=len(data["schools"]),
                foundation_contacts=data["contacts"],
                total_decision_makers=len(data["contacts"]),
                has_whatsapp=data["has_whatsapp"],
                has_linkedin=data["has_linkedin"],
                common_tech_stack=list(data["tech_stacks"]),
            )
            clusters.append(cluster)
        
        # Sort by number of schools (larger foundations first)
        clusters.sort(key=lambda x: x.total_schools, reverse=True)
        
        return clusters
    
    def export_foundation_clusters(
        self, 
        results: List[ProcessingResult], 
        filename: str = None
    ) -> str:
        """Export foundation clusters to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"foundation_clusters_{timestamp}.csv"
        
        filepath = config.OUTPUT_DIR / filename
        clusters = self.cluster_by_foundation(results)
        
        rows = []
        for cluster in clusters:
            rows.append({
                "Foundation": cluster.foundation_name,
                "Schools": ", ".join(cluster.schools),
                "Total Schools": cluster.total_schools,
                "Total Contacts": cluster.total_decision_makers,
                "Has WhatsApp": "✓" if cluster.has_whatsapp else "",
                "Has LinkedIn": "✓" if cluster.has_linkedin else "",
                "Tech Stack": ", ".join(cluster.common_tech_stack),
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        console.print(f"💾 [green]Foundation clusters exported to:[/green] {filepath}")
        console.print(f"   Total foundations: {len(clusters)}")
        
        return str(filepath)
    
    def print_summary(self, batch_result: BatchResult):
        """Print a beautiful summary of processing results"""
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]Processing Complete![/bold green]\n\n"
            f"Total Schools: {batch_result.total_schools}\n"
            f"Successful: {batch_result.successful}\n"
            f"Failed: {batch_result.failed}\n"
            f"Total Time: {batch_result.total_time_seconds:.1f}s",
            title="📊 Summary"
        ))
        
        # Decision makers found
        total_dms = sum(
            len(r.school_data.decision_makers) 
            for r in batch_result.results 
            if r.school_data
        )
        
        # WhatsApp found
        wa_count = sum(
            1 for r in batch_result.results 
            if r.school_data and r.school_data.whatsapp_business
        )
        
        # Create results table
        table = Table(title="Results Overview")
        table.add_column("School", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Decision Makers", justify="center")
        table.add_column("WhatsApp", justify="center")
        table.add_column("Quality", justify="center")
        
        for result in batch_result.results:
            if result.school_data:
                dm_count = len(result.school_data.decision_makers)
                wa = "✓" if result.school_data.whatsapp_business else "✗"
                quality = f"{result.school_data.data_quality_score:.0%}"
                status = "[green]✓[/green]"
            else:
                dm_count = 0
                wa = "✗"
                quality = "N/A"
                status = "[red]✗[/red]"
            
            table.add_row(
                result.school_input.name[:30],
                status,
                str(dm_count),
                wa,
                quality
            )
        
        console.print(table)
        
        console.print(f"\n📈 [bold]Stats:[/bold]")
        console.print(f"   Total Decision Makers Found: {total_dms}")
        console.print(f"   Schools with WhatsApp: {wa_count}/{batch_result.total_schools}")


async def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Indonesia EdTech Lead Gen Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                       # Process priority schools (Surabaya)
  python main.py --all                 # Process all schools
  python main.py --batch 5             # Process in batches of 5
  python main.py --location Jakarta    # Process Jakarta schools only
  python main.py --school "PPPK Petra" # Process single school
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Process all schools in the database"
    )
    parser.add_argument(
        "--priority",
        action="store_true",
        default=True,
        help="Process only priority schools (default)"
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Filter schools by location (e.g., Jakarta, Surabaya)"
    )
    parser.add_argument(
        "--school",
        type=str,
        help="Process a single school by name"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=5,
        help="Batch size for processing (default: 5)"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for batch processing (skip first N schools)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Delay between schools in seconds (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["csv", "excel", "both", "all"],
        default="both",
        help="Output format: csv, excel, both, or all (includes person-centric)"
    )
    parser.add_argument(
        "--person-leads",
        action="store_true",
        help="Also export person-centric leads (one row per person)"
    )
    parser.add_argument(
        "--clusters",
        action="store_true",
        help="Also export foundation clusters"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Print header
    console.print("\n" + "=" * 60)
    console.print("[bold blue]🇮🇩 Indonesia EdTech Lead Gen Engine[/bold blue]")
    console.print("=" * 60)
    
    # Validate configuration
    errors = Config.validate()
    if errors:
        console.print("\n[red]❌ Configuration errors:[/red]")
        for error in errors:
            console.print(f"   • {error}")
        console.print("\nPlease check your .env file and try again.")
        console.print("Copy env.example to .env and fill in your API keys.")
        return
    
    if args.validate:
        console.print("\n[green]✓ Configuration is valid![/green]")
        print_school_summary()
        return
    
    # Determine which schools to process
    if args.school:
        # Single school
        all_schools = get_all_schools()
        matching = [s for s in all_schools if args.school.lower() in s.name.lower()]
        if not matching:
            console.print(f"[red]School not found: {args.school}[/red]")
            return
        schools = matching[:1]
    elif args.location:
        schools = get_schools_by_location(args.location)
        if not schools:
            console.print(f"[red]No schools found for location: {args.location}[/red]")
            return
    elif args.all:
        schools = get_all_schools()
    else:
        schools = get_priority_schools()
    
    # Apply batch/offset (skip batch limit if --all is specified)
    if args.offset > 0:
        schools = schools[args.offset:]
    if not args.all and args.batch and args.batch < len(schools):
        schools = schools[:args.batch]
    
    console.print(f"\n📚 Schools to process: {len(schools)}")
    
    # Initialize engine and process
    engine = LeadEnrichmentEngine()
    
    batch_result = await engine.enrich_batch(
        schools=schools,
        delay_between_schools=args.delay
    )
    
    # Export results
    if batch_result.successful > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if args.output in ["csv", "both", "all"]:
            engine.export_to_csv(batch_result.results, f"leads_{timestamp}.csv")
        
        if args.output in ["excel", "both", "all"]:
            engine.export_to_excel(batch_result.results, f"leads_{timestamp}.xlsx")
        
        # NEW: Person-centric leads export
        if args.person_leads or args.output == "all":
            engine.export_person_leads(batch_result.results, f"person_leads_{timestamp}.csv")
            engine.export_person_leads_json(batch_result.results, f"person_leads_{timestamp}.json")
        
        # NEW: Foundation clusters export
        if args.clusters or args.output == "all":
            engine.export_foundation_clusters(batch_result.results, f"foundation_clusters_{timestamp}.csv")
    
    # Print summary
    engine.print_summary(batch_result)
    
    console.print(f"\n✅ [bold green]Done![/bold green] Check the output/ folder for results.\n")


if __name__ == "__main__":
    asyncio.run(main())

