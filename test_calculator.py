"""
Tests for the interest calculation functionality.
"""

import pytest
from datetime import datetime
from calculator import (
    calculate_interest,
    calculate_days,
    calculate_interest_with_details,
    format_currency,
    validate_calculation_inputs,
    calculate_tolerance,
    format_percentage,
    format_days,
    CalculationResult
)

def test_calculate_interest_basic():
    """Test basic interest calculation."""
    principal = 1000000.0  # $1M
    rate = 0.05  # 5%
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 4, 1)  # 91 days
    
    result = calculate_interest(principal, rate, start_date, end_date)
    expected = 1000000 * 0.05 * 91 / 360
    assert abs(result - expected) < 0.01

def test_calculate_days():
    """Test day calculation between dates."""
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    result = calculate_days(start, end)
    assert result == 30

def test_calculate_interest_with_details():
    """Test detailed interest calculation."""
    principal = 500000.0
    rate = 0.04
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)  # 31 days
    
    result = calculate_interest_with_details(principal, rate, start_date, end_date)
    
    assert isinstance(result, CalculationResult)
    assert result.expected_interest > 0
    assert result.days_calculated == 31
    assert "360" in result.formula_used

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1234567.89) == "$1,234,567.89"
    assert format_currency(0) == "$0.00"
    assert format_currency(-100) == "-$100.00"
    assert format_currency(None) == "N/A"

def test_validate_calculation_inputs():
    """Test input validation."""
    # Valid inputs
    errors = validate_calculation_inputs(
        100000.0, 0.05, datetime(2024, 1, 1), datetime(2024, 2, 1)
    )
    assert len(errors) == 0
    
    # Invalid principal
    errors = validate_calculation_inputs(
        -100000.0, 0.05, datetime(2024, 1, 1), datetime(2024, 2, 1)
    )
    assert 'principal' in errors
    
    # Invalid rate
    errors = validate_calculation_inputs(
        100000.0, -0.05, datetime(2024, 1, 1), datetime(2024, 2, 1)
    )
    assert 'rate' in errors
    
    # Invalid date range
    errors = validate_calculation_inputs(
        100000.0, 0.05, datetime(2024, 2, 1), datetime(2024, 1, 1)
    )
    assert 'date_range' in errors

def test_calculate_tolerance():
    """Test tolerance calculation."""
    # Small amount - should use $1 minimum
    assert calculate_tolerance(100) == 1.0
    
    # Large amount - should use 0.01%
    large_amount = 1000000
    expected_tolerance = large_amount * 0.0001
    assert calculate_tolerance(large_amount) == expected_tolerance

def test_format_percentage():
    """Test percentage formatting."""
    assert format_percentage(0.0525) == "5.2500%"
    assert format_percentage(0.1) == "10.0000%"
    assert format_percentage(None) == "N/A"

def test_format_days():
    """Test days formatting."""
    assert format_days(1) == "1 day"
    assert format_days(30) == "30 days"
    assert format_days(None) == "N/A"

if __name__ == "__main__":
    # Run basic tests
    test_calculate_interest_basic()
    test_calculate_days()
    test_calculate_interest_with_details()
    test_format_currency()
    test_validate_calculation_inputs()
    test_calculate_tolerance()
    test_format_percentage()
    test_format_days()
    print("All calculator tests passed!")