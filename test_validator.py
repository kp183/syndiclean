"""
Tests for the validation functionality.
"""

import pytest
from datetime import datetime
from validator import (
    calculate_tolerance,
    validate_interest_calculation,
    generate_validation_summary,
    get_validation_recommendations,
    format_validation_for_display,
    validate_extracted_data_completeness,
    can_perform_validation,
    ValidationResult
)
from calculator import CalculationResult
from extractor import ExtractedData

def create_sample_extracted_data():
    """Create sample extracted data for testing."""
    data = ExtractedData()
    data.principal_amount = 1000000.0
    data.interest_rate = 0.05
    data.start_date = datetime(2024, 1, 1)
    data.end_date = datetime(2024, 4, 1)
    data.notice_interest_amount = 12638.89
    return data

def create_sample_calculation_result():
    """Create sample calculation result for testing."""
    return CalculationResult(
        expected_interest=12638.89,
        days_calculated=91,
        formula_used="Interest = Principal × Rate × Days / 360",
        calculation_details={
            'principal': 1000000.0,
            'annual_rate': 0.05,
            'start_date': '01/01/2024',
            'end_date': '04/01/2024',
            'days': 91
        }
    )

def test_calculate_tolerance():
    """Test tolerance calculation."""
    # Small amount - should use $1 minimum
    assert calculate_tolerance(100) == 1.0
    
    # Large amount - should use 0.01%
    large_amount = 1000000
    expected_tolerance = large_amount * 0.0001
    assert calculate_tolerance(large_amount) == expected_tolerance
    
    # Zero or negative - should use $1
    assert calculate_tolerance(0) == 1.0
    assert calculate_tolerance(-100) == 1.0

def test_validate_interest_calculation_pass():
    """Test validation with matching amounts (PASS)."""
    extracted_data = create_sample_extracted_data()
    calculation_result = create_sample_calculation_result()
    
    result = validate_interest_calculation(extracted_data, calculation_result)
    
    assert isinstance(result, ValidationResult)
    assert result.status == "PASS"
    assert result.difference_amount == 0.0
    assert result.expected_amount == 12638.89
    assert result.notice_amount == 12638.89

def test_validate_interest_calculation_fail():
    """Test validation with mismatched amounts (FAIL)."""
    extracted_data = create_sample_extracted_data()
    extracted_data.notice_interest_amount = 15000.0  # Different amount
    calculation_result = create_sample_calculation_result()
    
    result = validate_interest_calculation(extracted_data, calculation_result)
    
    assert isinstance(result, ValidationResult)
    assert result.status == "FAIL"
    assert result.difference_amount > 0
    assert result.expected_amount == 12638.89
    assert result.notice_amount == 15000.0

def test_validate_interest_calculation_missing_data():
    """Test validation with missing required data."""
    extracted_data = create_sample_extracted_data()
    extracted_data.notice_interest_amount = None
    calculation_result = create_sample_calculation_result()
    
    with pytest.raises(ValueError, match="Notice interest amount is required"):
        validate_interest_calculation(extracted_data, calculation_result)

def test_generate_validation_summary():
    """Test validation summary generation."""
    extracted_data = create_sample_extracted_data()
    calculation_result = create_sample_calculation_result()
    validation_result = validate_interest_calculation(extracted_data, calculation_result)
    
    summary = generate_validation_summary(validation_result)
    
    assert "VALIDATION PASSED" in summary
    assert "AMOUNT COMPARISON:" in summary
    assert "EXPLANATION:" in summary

def test_get_validation_recommendations_pass():
    """Test recommendations for PASS result."""
    extracted_data = create_sample_extracted_data()
    calculation_result = create_sample_calculation_result()
    validation_result = validate_interest_calculation(extracted_data, calculation_result)
    
    recommendations = get_validation_recommendations(validation_result)
    
    assert len(recommendations) > 0
    assert any("ready to be sent" in rec.lower() for rec in recommendations)

def test_get_validation_recommendations_fail():
    """Test recommendations for FAIL result."""
    extracted_data = create_sample_extracted_data()
    extracted_data.notice_interest_amount = 15000.0
    calculation_result = create_sample_calculation_result()
    validation_result = validate_interest_calculation(extracted_data, calculation_result)
    
    recommendations = get_validation_recommendations(validation_result)
    
    assert len(recommendations) > 0
    assert any("review" in rec.lower() for rec in recommendations)

def test_format_validation_for_display():
    """Test validation formatting for display."""
    extracted_data = create_sample_extracted_data()
    calculation_result = create_sample_calculation_result()
    validation_result = validate_interest_calculation(extracted_data, calculation_result)
    
    display_info = format_validation_for_display(validation_result)
    
    assert "status_color" in display_info
    assert "status_icon" in display_info
    assert "status_text" in display_info
    assert display_info["status_text"] == "PASS"

def test_validate_extracted_data_completeness():
    """Test extracted data completeness validation."""
    # Complete data
    complete_data = create_sample_extracted_data()
    errors = validate_extracted_data_completeness(complete_data)
    assert len(errors) == 0
    
    # Missing principal
    incomplete_data = create_sample_extracted_data()
    incomplete_data.principal_amount = None
    errors = validate_extracted_data_completeness(incomplete_data)
    assert 'principal' in errors
    
    # Invalid date range
    invalid_data = create_sample_extracted_data()
    invalid_data.end_date = datetime(2023, 12, 1)  # Before start date
    errors = validate_extracted_data_completeness(invalid_data)
    assert 'date_range' in errors

def test_can_perform_validation():
    """Test validation feasibility check."""
    # Valid data
    extracted_data = create_sample_extracted_data()
    calculation_result = create_sample_calculation_result()
    
    can_validate, issues = can_perform_validation(extracted_data, calculation_result)
    assert can_validate is True
    assert len(issues) == 0
    
    # Missing calculation result
    can_validate, issues = can_perform_validation(extracted_data, None)
    assert can_validate is False
    assert len(issues) > 0

if __name__ == "__main__":
    # Run basic tests
    test_calculate_tolerance()
    test_validate_interest_calculation_pass()
    test_validate_interest_calculation_fail()
    test_generate_validation_summary()
    test_get_validation_recommendations_pass()
    test_get_validation_recommendations_fail()
    test_format_validation_for_display()
    test_validate_extracted_data_completeness()
    test_can_perform_validation()
    print("All validator tests passed!")