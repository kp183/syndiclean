"""
PDF Data Extraction Module

This module handles extraction of financial data from Interest Payment Notice PDFs.
It uses pdfplumber to parse PDF content and extract structured data including
principal amounts, interest rates, dates, and interest amounts.
"""

import pdfplumber
import re
from datetime import datetime
from typing import Dict, Any, Optional
import io

class ExtractedData:
    """Data class to hold extracted financial information from PDF."""
    
    def __init__(self):
        self.principal_amount: Optional[float] = None
        self.interest_rate: Optional[float] = None
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.notice_interest_amount: Optional[float] = None
        self.extraction_confidence: Dict[str, float] = {}

def extract_loan_data(pdf_file) -> ExtractedData:
    """
    Extract structured financial data from Interest Payment Notice PDF.
    
    Args:
        pdf_file: Uploaded PDF file object
        
    Returns:
        ExtractedData: Object containing extracted financial information
        
    Raises:
        Exception: If PDF cannot be processed or required data cannot be extracted
    """
    extracted_data = ExtractedData()
    
    try:
        # Reset file pointer to beginning
        pdf_file.seek(0)
        
        # Extract text from all pages of the PDF
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        
        if not full_text.strip():
            raise Exception("No text could be extracted from the PDF")
        
        # Extract principal amount
        principal = parse_currency_amount(full_text)
        if principal is not None:
            extracted_data.principal_amount = principal
            extracted_data.extraction_confidence['principal'] = 0.8
        
        # Extract interest rate
        rate = parse_percentage(full_text)
        if rate is not None:
            extracted_data.interest_rate = rate
            extracted_data.extraction_confidence['rate'] = 0.8
        
        # Extract dates
        dates = extract_dates(full_text)
        if len(dates) >= 2:
            # Assume first date is start date, second is end date
            extracted_data.start_date = dates[0]
            extracted_data.end_date = dates[1]
            extracted_data.extraction_confidence['dates'] = 0.7
        
        # Extract notice interest amount (look for interest amount patterns)
        interest_amount = extract_interest_amount(full_text)
        if interest_amount is not None:
            extracted_data.notice_interest_amount = interest_amount
            extracted_data.extraction_confidence['interest_amount'] = 0.8
        
        return extracted_data
        
    except Exception as e:
        raise Exception(f"Failed to extract data from PDF: {str(e)}")

def parse_currency_amount(text: str) -> Optional[float]:
    """
    Parse currency strings to numeric values, specifically looking for principal amounts.
    
    Args:
        text: String containing currency amount (e.g., "$1,234,567.89")
        
    Returns:
        float: Parsed numeric value or None if parsing fails
    """
    if not text:
        return None
    
    # More specific patterns that look for principal amounts near relevant keywords
    principal_patterns = [
        r'(?:principal\s*(?:amount)?)\s*:?\s*\$\s*([0-9,]+(?:\.[0-9]{2})?)',  # Principal: $1,234,567.89
        r'(?:loan\s+amount)\s*:?\s*\$\s*([0-9,]+(?:\.[0-9]{2})?)',  # Loan Amount: $1,234,567.89
        r'(?:outstanding\s+balance)\s*:?\s*\$\s*([0-9,]+(?:\.[0-9]{2})?)',  # Outstanding Balance: $1,234,567.89
    ]
    
    # Try principal-specific patterns first
    for pattern in principal_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                if 1000 <= amount <= 1_000_000_000:  # Reasonable principal range
                    return amount
            except (ValueError, IndexError):
                continue
    
    # Fallback to general currency patterns - handle both with and without commas
    general_patterns = [
        r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',  # $1,234,567.89 or $1234567.89
    ]
    
    amounts = []
    for pattern in general_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                # Filter for reasonable principal amounts and exclude account numbers
                if 1000 <= amount <= 100_000_000:
                    amounts.append(amount)
            except (ValueError, IndexError):
                continue
    
    # Return the largest reasonable amount found
    return max(amounts) if amounts else None

def parse_date(text: str) -> Optional[datetime]:
    """
    Parse various date formats to datetime objects.
    
    Args:
        text: String containing date in various formats
        
    Returns:
        datetime: Parsed date object or None if parsing fails
    """
    if not text:
        return None
    
    # Common date formats used in banking documents
    date_formats = [
        '%m/%d/%Y',      # 12/31/2023
        '%m-%d-%Y',      # 12-31-2023
        '%Y-%m-%d',      # 2023-12-31
        '%B %d, %Y',     # December 31, 2023
        '%b %d, %Y',     # Dec 31, 2023
        '%d %B %Y',      # 31 December 2023
        '%d %b %Y',      # 31 Dec 2023
        '%m/%d/%y',      # 12/31/23
        '%m-%d-%y',      # 12-31-23
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(text.strip(), date_format)
        except ValueError:
            continue
    
    return None

def extract_dates(text: str) -> list[datetime]:
    """
    Extract interest period dates from text using specific patterns.
    
    Args:
        text: Full text to search for dates
        
    Returns:
        list[datetime]: List of parsed datetime objects [start_date, end_date]
    """
    dates = []
    
    # Look for specific interest period date patterns first
    interest_date_patterns = [
        r'(?:interest\s+period\s+start\s+date|start\s+date)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(?:interest\s+period\s+end\s+date|end\s+date)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(?:from|start)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(?:to|through|end)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
    ]
    
    # Extract interest period specific dates
    interest_dates = []
    for pattern in interest_date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            date_str = match.group(1)
            parsed_date = parse_date(date_str)
            if parsed_date and parsed_date not in interest_dates:
                interest_dates.append(parsed_date)
    
    # If we found interest period dates, use those
    if len(interest_dates) >= 2:
        interest_dates.sort()
        return interest_dates[:2]  # Return first two (start and end)
    
    # Fallback to general date patterns, but exclude notice dates
    general_date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',          # MM/DD/YYYY
        r'\b(\d{1,2}-\d{1,2}-\d{4})\b',          # MM-DD-YYYY
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',          # YYYY-MM-DD
        r'\b([A-Za-z]+ \d{1,2}, \d{4})\b',       # Month DD, YYYY
        r'\b(\d{1,2} [A-Za-z]+ \d{4})\b',        # DD Month YYYY
    ]
    
    all_dates = []
    for pattern in general_date_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            date_str = match.group(1)
            parsed_date = parse_date(date_str)
            if parsed_date and parsed_date not in all_dates:
                # Skip dates that are likely notice dates (look for "notice date" context)
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].lower()
                
                if "notice" not in context and "reference" not in context:
                    all_dates.append(parsed_date)
    
    # Sort dates chronologically and return first two
    all_dates.sort()
    return all_dates[:2] if len(all_dates) >= 2 else all_dates

def parse_percentage(text: str) -> Optional[float]:
    """
    Parse percentage strings to decimal values.
    
    Args:
        text: String containing percentage (e.g., "5.25%")
        
    Returns:
        float: Decimal representation (e.g., 0.0525) or None if parsing fails
    """
    if not text:
        return None
    
    # Regex patterns for percentage values
    percentage_patterns = [
        r'(\d+\.?\d*)\s*%',                                    # 5.25%
        r'(\d+\.?\d*)\s*percent',                              # 5.25 percent
        r'(?:rate|interest)\s*:?\s*(\d+\.?\d*)\s*%',          # Rate: 5.25%
        r'(\d+\.?\d*)\s*(?:per\s*cent|pct)',                  # 5.25 per cent
    ]
    
    percentages = []
    for pattern in percentage_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                percentage_str = match.group(1)
                percentage = float(percentage_str)
                # Convert percentage to decimal (5.25% -> 0.0525)
                decimal_value = percentage / 100.0
                # Filter reasonable interest rates (0.1% to 50%)
                if 0.001 <= decimal_value <= 0.5:
                    percentages.append(decimal_value)
            except (ValueError, IndexError):
                continue
    
    # Return the first reasonable percentage found
    return percentages[0] if percentages else None

def extract_interest_amount(text: str) -> Optional[float]:
    """
    Extract interest amount from text, looking for specific patterns.
    
    Args:
        text: Full text to search for interest amounts
        
    Returns:
        float: Interest amount or None if not found
    """
    if not text:
        return None
    
    # Patterns specifically for interest amounts
    interest_patterns = [
        r'(?:interest\s+(?:amount|payment|due))\s*:?\s*\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)',
        r'(?:total\s+interest)\s*:?\s*\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)',
        r'(?:interest\s+calculated)\s*:?\s*\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)',
        r'(?:accrued\s+interest)\s*:?\s*\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)',
    ]
    
    amounts = []
    for pattern in interest_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                # Interest amounts should be reasonable (not too small, not larger than principal)
                if 1 <= amount <= 10000000:  # $1 to $10M
                    amounts.append(amount)
            except (ValueError, IndexError):
                continue
    
    # Return the first reasonable interest amount found
    return amounts[0] if amounts else None