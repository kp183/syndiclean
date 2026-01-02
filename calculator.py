"""
Interest Calculation Module

This module implements standard banking interest calculations using the 360-day
convention commonly used in commercial lending. It provides functions for
calculating interest amounts, date differences, and currency formatting.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CalculationResult:
    """Data class to hold interest calculation results and details."""
    expected_interest: float
    days_calculated: int
    formula_used: str
    calculation_details: Dict[str, Any]


def calculate_interest(principal: float, rate: float, start_date: datetime, end_date: datetime) -> float:
    """
    Calculate interest using the standard banking 360-day convention.
    
    Formula: Interest = Principal × Annual_Rate × Days / 360
    
    Args:
        principal: Loan amount in dollars
        rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
        start_date: Interest calculation start date
        end_date: Interest calculation end date
        
    Returns:
        float: Calculated interest amount
        
    Raises:
        ValueError: If inputs are invalid (negative amounts, invalid dates, etc.)
    """
    # Validate inputs
    if principal <= 0:
        raise ValueError("Principal amount must be positive")
    
    if rate < 0:
        raise ValueError("Interest rate cannot be negative")
    
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")
    
    # Calculate days between dates
    days = calculate_days(start_date, end_date)
    
    # Apply banking formula: Interest = Principal × Rate × Days / 360
    interest = principal * rate * days / 360.0
    
    return round(interest, 2)


def calculate_days(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate the number of days between two dates.
    
    Uses calendar days (actual/360 convention) which counts the actual
    number of days between the start and end dates.
    
    Args:
        start_date: Starting date for calculation
        end_date: Ending date for calculation
        
    Returns:
        int: Number of days between dates
        
    Raises:
        ValueError: If start_date is not before end_date
    """
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")
    
    # Calculate difference and return days
    delta = end_date - start_date
    return delta.days


def calculate_interest_with_details(principal: float, rate: float, start_date: datetime, end_date: datetime) -> CalculationResult:
    """
    Calculate interest with detailed breakdown of the calculation.
    
    Args:
        principal: Loan amount in dollars
        rate: Annual interest rate as decimal
        start_date: Interest calculation start date
        end_date: Interest calculation end date
        
    Returns:
        CalculationResult: Object containing calculation results and details
    """
    # Calculate interest
    interest = calculate_interest(principal, rate, start_date, end_date)
    days = calculate_days(start_date, end_date)
    
    # Create detailed calculation breakdown
    calculation_details = {
        'principal': principal,
        'annual_rate': rate,
        'annual_rate_percentage': rate * 100,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
        'days': days,
        'day_count_convention': '360-day',
        'formula': 'Interest = Principal × Rate × Days / 360',
        'calculation_steps': {
            'step_1': f'Principal = {format_currency(principal)}',
            'step_2': f'Annual Rate = {rate * 100:.4f}%',
            'step_3': f'Days = {days}',
            'step_4': f'Interest = {format_currency(principal)} × {rate:.6f} × {days} / 360',
            'step_5': f'Interest = {format_currency(interest)}'
        }
    }
    
    return CalculationResult(
        expected_interest=interest,
        days_calculated=days,
        formula_used='Interest = Principal × Rate × Days / 360',
        calculation_details=calculation_details
    )


def format_currency(amount: float) -> str:
    """
    Format amounts for display with proper currency formatting.
    
    Args:
        amount: Numeric amount to format
        
    Returns:
        str: Formatted currency string (e.g., "$1,234,567.89")
    """
    if amount is None:
        return "N/A"
    
    # Handle negative amounts
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    
    return f"${amount:,.2f}"


def validate_calculation_inputs(principal: Optional[float], rate: Optional[float], 
                              start_date: Optional[datetime], end_date: Optional[datetime]) -> Dict[str, str]:
    """
    Validate inputs for interest calculation and return any error messages.
    
    Args:
        principal: Principal amount to validate
        rate: Interest rate to validate
        start_date: Start date to validate
        end_date: End date to validate
        
    Returns:
        Dict[str, str]: Dictionary of field names to error messages (empty if all valid)
    """
    errors = {}
    
    # Validate principal
    if principal is None:
        errors['principal'] = "Principal amount is required"
    elif principal <= 0:
        errors['principal'] = "Principal amount must be positive"
    elif principal > 1_000_000_000:  # $1 billion limit
        errors['principal'] = "Principal amount seems unreasonably large"
    
    # Validate interest rate
    if rate is None:
        errors['rate'] = "Interest rate is required"
    elif rate < 0:
        errors['rate'] = "Interest rate cannot be negative"
    elif rate > 1.0:  # 100% rate limit
        errors['rate'] = "Interest rate seems unreasonably high (over 100%)"
    
    # Validate dates
    if start_date is None:
        errors['start_date'] = "Start date is required"
    if end_date is None:
        errors['end_date'] = "End date is required"
    
    if start_date and end_date:
        if start_date >= end_date:
            errors['date_range'] = "Start date must be before end date"
        
        # Check for reasonable date ranges (not more than 10 years)
        if (end_date - start_date).days > 3650:
            errors['date_range'] = "Date range seems unreasonably long (over 10 years)"
    
    return errors


def calculate_tolerance(amount: float) -> float:
    """
    Calculate acceptable tolerance for interest amount comparison.
    
    Uses the larger of $1.00 or 0.01% of the amount as tolerance.
    
    Args:
        amount: Interest amount to calculate tolerance for
        
    Returns:
        float: Tolerance amount
    """
    if amount <= 0:
        return 1.0  # Minimum $1 tolerance
    
    # Calculate 0.01% of amount
    percentage_tolerance = amount * 0.0001
    
    # Return the larger of $1 or 0.01%
    return max(1.0, percentage_tolerance)


def format_percentage(rate: float) -> str:
    """
    Format interest rate for display.
    
    Args:
        rate: Interest rate as decimal (e.g., 0.0525)
        
    Returns:
        str: Formatted percentage string (e.g., "5.2500%")
    """
    if rate is None:
        return "N/A"
    
    return f"{rate * 100:.4f}%"


def format_days(days: int) -> str:
    """
    Format days count for display.
    
    Args:
        days: Number of days
        
    Returns:
        str: Formatted days string
    """
    if days is None:
        return "N/A"
    
    if days == 1:
        return "1 day"
    else:
        return f"{days} days"