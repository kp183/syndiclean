"""
Tests for the PDF extraction functionality.
"""

import pytest
from unittest.mock import Mock, patch
from extractor import (
    extract_loan_data, 
    parse_currency_amount, 
    parse_percentage, 
    parse_date, 
    extract_dates,
    extract_interest_amount,
    ExtractedData
)
from datetime import datetime
import io

def test_parse_currency_amount():
    """Test currency amount parsing with various formats."""
    # Test standard currency format
    assert parse_currency_amount("$1,234,567.89") == 1234567.89
    
    # Test without commas
    assert parse_currency_amount("$1234567.89") == 1234567.89
    
    # Test with text context
    assert parse_currency_amount("Principal: $5,000,000.00") == 5000000.00
    
    # Test with no valid currency
    assert parse_currency_amount("No money here") is None
    
    # Test empty string
    assert parse_currency_amount("") is None

def test_parse_percentage():
    """Test percentage parsing with various formats."""
    # Test standard percentage
    assert parse_percentage("5.25%") == 0.0525
    
    # Test with context
    assert parse_percentage("Interest Rate: 4.75%") == 0.0475
    
    # Test with spaces
    assert parse_percentage("3.5 %") == 0.035
    
    # Test no percentage
    assert parse_percentage("No rate here") is None
    
    # Test empty string
    assert parse_percentage("") is None

def test_parse_date():
    """Test date parsing with various formats."""
    # Test MM/DD/YYYY format
    result = parse_date("12/31/2023")
    assert result == datetime(2023, 12, 31)
    
    # Test MM-DD-YYYY format
    result = parse_date("01-15-2024")
    assert result == datetime(2024, 1, 15)
    
    # Test invalid date
    assert parse_date("invalid date") is None
    
    # Test empty string
    assert parse_date("") is None

def test_extract_dates():
    """Test extracting multiple dates from text."""
    text = "Start Date: 01/01/2024 End Date: 03/31/2024"
    dates = extract_dates(text)
    
    assert len(dates) == 2
    assert dates[0] == datetime(2024, 1, 1)
    assert dates[1] == datetime(2024, 3, 31)

def test_extract_interest_amount():
    """Test extracting interest amounts from text."""
    # Test with clear interest amount
    text = "Interest Amount: $12,345.67"
    result = extract_interest_amount(text)
    assert result == 12345.67
    
    # Test with total interest
    text = "Total Interest: $8,500.00"
    result = extract_interest_amount(text)
    assert result == 8500.00
    
    # Test with no interest amount
    text = "No interest information here"
    result = extract_interest_amount(text)
    assert result is None

@patch('pdfplumber.open')
def test_extract_loan_data_success(mock_pdf_open):
    """Test successful data extraction from PDF."""
    # Mock PDF content
    mock_page = Mock()
    mock_page.extract_text.return_value = """
    Loan Interest Payment Notice
    Principal Amount: $1,000,000.00
    Interest Rate: 5.25%
    Start Date: 01/01/2024
    End Date: 03/31/2024
    Interest Amount: $13,125.00
    """
    
    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdf_open.return_value = mock_pdf
    
    # Mock file object
    mock_file = Mock()
    mock_file.seek = Mock()
    
    # Test extraction
    result = extract_loan_data(mock_file)
    
    # Verify results
    assert isinstance(result, ExtractedData)
    assert result.principal_amount == 1000000.00
    assert result.interest_rate == 0.0525
    assert result.notice_interest_amount == 13125.00
    assert result.start_date == datetime(2024, 1, 1)
    assert result.end_date == datetime(2024, 3, 31)

@patch('pdfplumber.open')
def test_extract_loan_data_empty_pdf(mock_pdf_open):
    """Test extraction from empty PDF."""
    # Mock empty PDF
    mock_page = Mock()
    mock_page.extract_text.return_value = ""
    
    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdf_open.return_value = mock_pdf
    
    # Mock file object
    mock_file = Mock()
    mock_file.seek = Mock()
    
    # Test extraction should raise exception
    with pytest.raises(Exception, match="No text could be extracted"):
        extract_loan_data(mock_file)

@patch('pdfplumber.open')
def test_extract_loan_data_partial_data(mock_pdf_open):
    """Test extraction with partial data available."""
    # Mock PDF with only some data
    mock_page = Mock()
    mock_page.extract_text.return_value = """
    Loan Document
    Principal Amount: $500,000.00
    Interest Rate: 4.5%
    Some other text without dates or interest amount
    """
    
    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdf_open.return_value = mock_pdf
    
    # Mock file object
    mock_file = Mock()
    mock_file.seek = Mock()
    
    # Test extraction
    result = extract_loan_data(mock_file)
    
    # Verify partial results
    assert isinstance(result, ExtractedData)
    assert result.principal_amount == 500000.00
    assert result.interest_rate == 0.045
    assert result.notice_interest_amount is None  # Not found
    assert result.start_date is None  # Not found
    assert result.end_date is None  # Not found

if __name__ == "__main__":
    # Run tests
    test_parse_currency_amount()
    test_parse_percentage()
    test_parse_date()
    test_extract_dates()
    test_extract_interest_amount()
    print("All extractor tests passed!")