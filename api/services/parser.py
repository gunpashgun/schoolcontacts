"""
Input parser for multiple formats (text, CSV, JSON, Excel)
"""
import re
import csv
import json
from typing import List, Optional
from io import StringIO, BytesIO
from models import SchoolInput
import logging

logger = logging.getLogger(__name__)


class InputParser:
    """Parse schools input from various formats"""
    
    @staticmethod
    def parse_text(text: str) -> List[SchoolInput]:
        """
        Parse plain text format: "Name - Type (Description)"
        
        Example:
        PPPK Petra - Private Christian (Elementary to High School, Education Board/Group)
        Yohanes Gabriel Foundation - Private Catholic (Elementary to High School, Religious Foundation)
        """
        schools = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern: "Name - Type (Description)"
            # Or: "Name - Type"
            match = re.match(r'^(.+?)\s*-\s*(.+?)(?:\s*\((.+?)\))?$', line)
            if match:
                name = match.group(1).strip()
                school_type = match.group(2).strip()
                notes = match.group(3).strip() if match.group(3) else None
                
                # Try to extract location from notes or type
                location = "Unknown"
                if notes:
                    # Look for common city names
                    cities = ["Jakarta", "Surabaya", "Bandung", "Semarang", "Bali", "Yogyakarta"]
                    for city in cities:
                        if city in notes:
                            location = city
                            break
                
                schools.append(SchoolInput(
                    name=name,
                    type=school_type,
                    location=location,
                    notes=notes
                ))
            else:
                # Fallback: treat entire line as name
                schools.append(SchoolInput(
                    name=line,
                    type="Unknown",
                    location="Unknown"
                ))
        
        return schools
    
    @staticmethod
    def parse_csv(csv_content: str | bytes) -> List[SchoolInput]:
        """Parse CSV format with columns: name, type, location"""
        schools = []
        reader = csv.DictReader(StringIO(csv_content))
        
        for row in reader:
            name = row.get('name', '').strip()
            school_type = row.get('type', row.get('school_type', 'Unknown')).strip()
            location = row.get('location', 'Unknown').strip()
            notes = row.get('notes', '').strip() or None
            
            if name:
                schools.append(SchoolInput(
                    name=name,
                    type=school_type or "Unknown",
                    location=location or "Unknown",
                    notes=notes
                ))
        
        return schools
    
    @staticmethod
    def parse_json(json_content: str) -> List[SchoolInput]:
        """Parse JSON array of school objects"""
        try:
            data = json.loads(json_content)
            schools = []
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        schools.append(SchoolInput(
                            name=item.get('name', '').strip(),
                            type=item.get('type', item.get('school_type', 'Unknown')).strip(),
                            location=item.get('location', 'Unknown').strip(),
                            notes=item.get('notes', '').strip() or None
                        ))
            
            return schools
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
    
    @staticmethod
    def parse_excel(file_content: bytes) -> List[SchoolInput]:
        """Parse Excel file"""
        try:
            import pandas as pd
            
            df = pd.read_excel(BytesIO(file_content))
            schools = []
            
            # Try to find name, type, location columns (case-insensitive)
            name_col = None
            type_col = None
            location_col = None
            notes_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'name' in col_lower and not name_col:
                    name_col = col
                elif 'type' in col_lower and not type_col:
                    type_col = col
                elif 'location' in col_lower and not location_col:
                    location_col = col
                elif 'notes' in col_lower or 'description' in col_lower:
                    notes_col = col
            
            if not name_col:
                raise ValueError("No 'name' column found in Excel file")
            
            for _, row in df.iterrows():
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                school_type = str(row[type_col]).strip() if type_col and pd.notna(row[type_col]) else "Unknown"
                location = str(row[location_col]).strip() if location_col and pd.notna(row[location_col]) else "Unknown"
                notes = str(row[notes_col]).strip() if notes_col and pd.notna(row[notes_col]) else None
                
                if name:
                    schools.append(SchoolInput(
                        name=name,
                        type=school_type,
                        location=location,
                        notes=notes
                    ))
            
            return schools
        except Exception as e:
            logger.error(f"Excel parse error: {e}")
            return []
    
    @staticmethod
    def parse(file_content: str | bytes, format_type: str) -> List[SchoolInput]:
        """
        Parse input based on format type
        
        Args:
            file_content: Content as string or bytes
            format_type: 'text', 'csv', 'json', or 'excel'
        """
        if format_type == 'text':
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            return InputParser.parse_text(file_content)
        elif format_type == 'csv':
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            return InputParser.parse_csv(file_content)
        elif format_type == 'json':
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            return InputParser.parse_json(file_content)
        elif format_type == 'excel':
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            return InputParser.parse_excel(file_content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

