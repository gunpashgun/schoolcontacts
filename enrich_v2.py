#!/usr/bin/env python3
"""
Enhanced Lead Enrichment v2
- Uses alternative school names
- More targeted searches for decision makers
- Better LinkedIn scraping
- Deeper website crawling
"""

import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
import httpx
import re
import json
from typing import List, Dict, Optional

from config import config
from models import SchoolInput, SchoolData, DecisionMaker
from search import SerperSearch
from scraper import WebScraper

from rich.console import Console
from rich.progress import Progress

console = Console()

# Alternative names for schools (helps find more results)
SCHOOL_ALIASES = {
    "PPPK Petra": ["Sekolah Petra", "Sekolah Kristen Petra", "SD Kristen Petra", "SMA Kristen Petra"],
    "Yohanes Gabriel Foundation": ["SDK Yohanes Gabriel", "SMP Yohanes Gabriel", "Yayasan Yohanes Gabriel"],
    "Santa Clara Catholic School": ["SDK Santa Clara", "Santa Clara Surabaya"],
    "Gloria Christian School": ["Sekolah Gloria", "Gloria Bilingual School"],
    "Stella Maris School": ["Stella Maris Surabaya", "SDK Stella Maris"],
    "Sekolah Dian Harapan": ["SDH", "Dian Harapan School"],
    "Sekolah Pelita Harapan": ["SPH", "Pelita Harapan"],
    "BINUS School": ["Binus School Simprug", "Binus School Serpong", "Binus School Bekasi"],
    "BPK Penabur": ["Penabur Jakarta", "SDK Penabur", "SMAK Penabur"],
    "Tarakanita": ["SDK Tarakanita", "SMP Tarakanita", "Sekolah Tarakanita"],
    "Al Azhar Islamic School": ["Al Azhar Jakarta", "SD Islam Al Azhar"],
    "Singapore Intercultural School": ["SIS Kelapa Gading", "SIS Bona Vista", "SIS Cilegon"],
    "Jakarta Intercultural School": ["JIS Jakarta", "JIS Cilandak", "JIS Pattimura"],
    "Sekolah Cikal": ["Cikal Amri", "Cikal Serpong", "Cikal Surabaya"],
    "ACG School Jakarta": ["ACG Jakarta"],
    "Australian Independent School": ["AIS Jakarta", "AIS Indonesia"],
    "Bina Bangsa School": ["BBS School", "Bina Bangsa Semarang"],
    "BTB School": ["Bina Tunas Bangsa", "BTB Depok"],
    "Sekolah Cita Buana": ["Cita Buana", "SCB Jakarta"],
    "Mawar Sharon Christian School": ["MSCS", "Mawar Sharon"],
    "Tzu Chi School": ["Sekolah Tzu Chi", "Tzu Chi Indonesia"],
    "Marie Joseph School": ["Sekolah Marie Joseph", "Marjo School"],
}

# Enhanced search queries
ENHANCED_SEARCHES = {
    # Find specific people on LinkedIn
    "linkedin_principal": '"{school}" "Kepala Sekolah" site:linkedin.com',
    "linkedin_director": '"{school}" ("Direktur" OR "Director") site:linkedin.com',
    "linkedin_academic": '"{school}" ("Academic" OR "Curriculum" OR "Akademik") site:linkedin.com',
    "linkedin_admission": '"{school}" ("Admission" OR "Pendaftaran") site:linkedin.com',
    "linkedin_it": '"{school}" ("IT" OR "Technology" OR "ICT") site:linkedin.com',
    
    # Find organization structure
    "struktur": '"{school}" ("struktur organisasi" OR "pengurus yayasan" OR "board of directors")',
    "team_page": '"{school}" ("our team" OR "meet the team" OR "faculty" OR "leadership")',
    
    # Find contact info directly
    "whatsapp_direct": '"{school}" wa.me',
    "contact_page": 'site:{domain} (contact OR hubungi OR kontak)',
    "about_page": 'site:{domain} (about OR tentang OR profil)',
}


class EnhancedEnricher:
    """Enhanced enrichment with alternative searches"""
    
    def __init__(self):
        self.search = SerperSearch()
        self.scraper = WebScraper()
        
    async def enrich_with_aliases(self, school_name: str, location: str) -> Dict:
        """Search using alternative school names"""
        all_results = {}
        
        # Get aliases
        aliases = SCHOOL_ALIASES.get(school_name, [])
        search_names = [school_name] + aliases
        
        console.print(f"\n🔍 Searching with {len(search_names)} name variations...")
        
        for name in search_names[:3]:  # Limit to 3 variations
            # LinkedIn searches
            for key in ["linkedin_principal", "linkedin_director", "linkedin_academic"]:
                query = ENHANCED_SEARCHES[key].format(school=name)
                results = await self.search.search(query, num_results=5)
                
                for r in results:
                    if r.url not in [x.url for x in all_results.get(key, [])]:
                        all_results.setdefault(key, []).append(r)
                
                await asyncio.sleep(0.3)
        
        return all_results
    
    async def extract_linkedin_profiles(self, search_results: Dict) -> List[Dict]:
        """Extract decision maker info from LinkedIn search results"""
        profiles = []
        
        for key, results in search_results.items():
            for result in results:
                if 'linkedin.com/in/' in result.url:
                    # Extract name from title (usually "Name - Title | LinkedIn")
                    name_match = re.match(r'^([^-|]+)', result.title)
                    name = name_match.group(1).strip() if name_match else ""
                    
                    # Extract role from title or snippet
                    role = ""
                    role_keywords = ["Kepala", "Principal", "Director", "Direktur", 
                                   "Academic", "Coordinator", "Manager", "Head"]
                    
                    for kw in role_keywords:
                        if kw.lower() in result.title.lower() or kw.lower() in result.snippet.lower():
                            # Try to extract full role
                            title_parts = result.title.split(' - ')
                            if len(title_parts) > 1:
                                role = title_parts[1].split(' | ')[0].strip()
                            break
                    
                    if name and len(name) > 2:
                        profiles.append({
                            "name": name,
                            "role": role,
                            "linkedin_url": result.url,
                            "source": result.snippet[:200]
                        })
        
        # Deduplicate by name
        seen_names = set()
        unique_profiles = []
        for p in profiles:
            name_lower = p['name'].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_profiles.append(p)
        
        return unique_profiles
    
    async def deep_scrape_website(self, url: str) -> Dict:
        """Deep scrape a school website for contacts"""
        contacts = {
            "emails": [],
            "whatsapp": [],
            "phones": [],
            "social": {}
        }
        
        if not url:
            return contacts
        
        try:
            pages = await self.scraper.scrape_school_website(url, max_pages=8)
            
            for page in pages:
                if page.success:
                    # Extract all contact types
                    contacts["emails"].extend(self.scraper.extract_emails(page.text_content))
                    contacts["whatsapp"].extend(self.scraper.extract_whatsapp_links(page.text_content + page.html_content))
                    contacts["phones"].extend(self.scraper.extract_all_phone_numbers(page.text_content))
                    
                    # Social media
                    social = self.scraper.extract_social_media(page.html_content)
                    contacts["social"].update(social)
            
            # Deduplicate
            contacts["emails"] = list(set(contacts["emails"]))
            contacts["whatsapp"] = list(set(contacts["whatsapp"]))
            contacts["phones"] = list(set(contacts["phones"]))
            
        except Exception as e:
            console.print(f"[red]Scrape error: {e}[/red]")
        
        return contacts


async def main():
    """Re-enrich schools with low quality scores"""
    
    console.print("\n" + "=" * 60)
    console.print("🔄 [bold blue]Enhanced Lead Enrichment v2[/bold blue]")
    console.print("=" * 60)
    
    # Load existing data
    df = pd.read_csv('output/leads_FULL_51_schools.csv')
    
    # Find schools that need enrichment (quality < 50% or missing key data)
    needs_enrichment = df[
        (df['Data Quality'].str.rstrip('%').astype(float) < 50) |
        (df['WhatsApp Business'].isna()) |
        (df['Official Email'].isna())
    ]
    
    console.print(f"\n📊 Schools needing enrichment: {len(needs_enrichment)}")
    
    enricher = EnhancedEnricher()
    
    # Process each school
    updates = []
    
    for idx, row in needs_enrichment.iterrows():
        school_name = row['School Name']
        location = row['Location']
        
        console.print(f"\n🏫 [bold]{school_name}[/bold] (current quality: {row['Data Quality']})")
        
        try:
            # Search with aliases
            search_results = await enricher.enrich_with_aliases(school_name, location)
            
            # Extract LinkedIn profiles
            profiles = await enricher.extract_linkedin_profiles(search_results)
            
            if profiles:
                console.print(f"   ✓ Found {len(profiles)} new LinkedIn profiles")
                for p in profiles[:3]:
                    console.print(f"      • {p['name']} - {p['role']}")
            
            # Deep scrape website if we have one
            website = row['Official Website'] if pd.notna(row['Official Website']) else ""
            
            if website and 'http' in website:
                console.print(f"   🌐 Deep scraping {website[:40]}...")
                contacts = await enricher.deep_scrape_website(website)
                
                if contacts['whatsapp']:
                    console.print(f"   ✓ Found WhatsApp: {contacts['whatsapp'][0]}")
                if contacts['emails']:
                    console.print(f"   ✓ Found emails: {len(contacts['emails'])}")
            else:
                contacts = {"emails": [], "whatsapp": [], "phones": [], "social": {}}
            
            updates.append({
                "index": idx,
                "school": school_name,
                "new_profiles": profiles,
                "new_contacts": contacts
            })
            
        except Exception as e:
            console.print(f"   [red]Error: {e}[/red]")
        
        # Rate limiting
        await asyncio.sleep(2)
    
    # Apply updates to dataframe
    console.print("\n" + "=" * 60)
    console.print("📝 Applying updates...")
    
    for update in updates:
        idx = update['index']
        
        # Add new profiles to DM columns
        profiles = update['new_profiles']
        for i, p in enumerate(profiles[:8], 1):  # Up to 8 DMs
            dm_name_col = f'DM{i} Name'
            dm_role_col = f'DM{i} Role'
            dm_li_col = f'DM{i} LinkedIn'
            
            # Only add if column is empty
            if dm_name_col in df.columns:
                if pd.isna(df.loc[idx, dm_name_col]) or df.loc[idx, dm_name_col] == '':
                    df.loc[idx, dm_name_col] = p['name']
                    df.loc[idx, dm_role_col] = p['role']
                    df.loc[idx, dm_li_col] = p['linkedin_url']
        
        # Add new contacts
        contacts = update['new_contacts']
        
        if contacts['whatsapp'] and (pd.isna(df.loc[idx, 'WhatsApp Business']) or df.loc[idx, 'WhatsApp Business'] == ''):
            df.loc[idx, 'WhatsApp Business'] = contacts['whatsapp'][0]
        
        if contacts['emails'] and (pd.isna(df.loc[idx, 'Official Email']) or df.loc[idx, 'Official Email'] == ''):
            df.loc[idx, 'Official Email'] = contacts['emails'][0]
        
        if contacts['social'].get('instagram') and (pd.isna(df.loc[idx, 'Instagram']) or df.loc[idx, 'Instagram'] == ''):
            df.loc[idx, 'Instagram'] = contacts['social']['instagram']
    
    # Save updated file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f'output/leads_ENRICHED_{timestamp}.csv'
    output_xlsx = f'output/leads_ENRICHED_{timestamp}.xlsx'
    
    df.to_csv(output_csv, index=False)
    df.to_excel(output_xlsx, index=False)
    
    console.print(f"\n💾 Saved to:")
    console.print(f"   {output_csv}")
    console.print(f"   {output_xlsx}")
    
    # Show summary
    console.print("\n" + "=" * 60)
    console.print("📊 ENRICHMENT SUMMARY")
    console.print("=" * 60)
    
    total_new_profiles = sum(len(u['new_profiles']) for u in updates)
    total_new_wa = sum(1 for u in updates if u['new_contacts']['whatsapp'])
    total_new_emails = sum(1 for u in updates if u['new_contacts']['emails'])
    
    console.print(f"   Schools processed: {len(updates)}")
    console.print(f"   New LinkedIn profiles: {total_new_profiles}")
    console.print(f"   New WhatsApp numbers: {total_new_wa}")
    console.print(f"   New emails: {total_new_emails}")
    
    console.print("\n✅ [bold green]Enrichment complete![/bold green]\n")


if __name__ == "__main__":
    asyncio.run(main())

