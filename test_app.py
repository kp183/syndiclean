"""
Basic tests for the LoanGuard application setup.
"""

import pytest
from unittest.mock import Mock
from app import validate_pdf_file

def test_validate_pdf_file_with_valid_pdf():
    """Test PDF validation with a valid PDF file."""
    # Mock a valid PDF file
    mock_file = Mock()
    mock_file.name = "test_document.pdf"
    mock_file.type = "application/pdf"
    
    result = validate_pdf_file(mock_file)
    assert result is True

def test_validate_pdf_file_with_invalid_extension():
    """Test PDF validation with invalid file extension."""
    # Mock a file with wrong extension
    mock_file = Mock()
    mock_file.name = "test_document.txt"
    mock_file.type = "text/plain"
    
    result = validate_pdf_file(mock_file)
    assert result is False

def test_validate_pdf_file_with_invalid_mime_type():
    """Test PDF validation with invalid MIME type."""
    # Mock a file with PDF extension but wrong MIME type
    mock_file = Mock()
    mock_file.name = "test_document.pdf"
    mock_file.type = "text/plain"
    
    result = validate_pdf_file(mock_file)
    assert result is False

def test_validate_pdf_file_with_none():
    """Test PDF validation with None input."""
    result = validate_pdf_file(None)
    assert result is False

if __name__ == "__main__":
    # Run basic tests
    test_validate_pdf_file_with_valid_pdf()
    test_validate_pdf_file_with_invalid_extension()
    test_validate_pdf_file_with_invalid_mime_type()
    test_validate_pdf_file_with_none()
    print("All basic tests passed!")