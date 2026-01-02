"""
Comprehensive Input Validation Module

This module provides comprehensive validation for all input data including
date formats, numeric values, and required field completeness. It ensures
data integrity and provides clear error messages for banking-grade validation.
"""

from datetime import datetime, date
from typing import Optional, Dict, List, Any, Tuple
import re
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Data class to hold validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Data class to hold comprehensive validation results."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    validated_data: Dict[str, Any]


def validate_date_format_and_range(date_value: Optional[datetime], field_name: str) -> List[ValidationError]:
    """
    Validate date format and check if date is within reasonable range.
    
    Args:
        date_value: Date to validate
        field_name: Name of the field being validated
        
    Returns:
        List[ValidationError]: List of validation errors (empty if valid)
    """
    errors = []
    
    if date_value is None:
        errors.append(ValidationError(
            field=field_name,
            message=f"{field_name} is required",
            severity="error",
            suggestion="Ensure the PDF contains a clearly marked date in MM/DD/YYYY format"
        ))
        return errors
    
    # Check if date is within reasonable range (not too far in past or future)
    current_year = datetime.now().year
    min_year = current_year - 50  # 50 years ago
    max_year = current_year + 10  # 10 years in future
    
    if date_value.year < min_year:
        errors.append(ValidationError(
            field=field_name,
            message=f"{field_name} is too far in the past ({date_value.year})",
            severity="error",
            suggestion=f"Date should be between {min_year} and {max_year}"
        ))
    
    if date_value.year > max_year:
        errors.append(ValidationError(
            field=field_name,
            message=f"{field_name} is too far in the future ({date_value.year})",
            severity="error",
            suggestion=f"Date should be between {min_year} and {max_year}"
        ))
    
    # Check for weekend dates (warning only, as some banks do use weekend dates)
    if date_value.weekday() >= 5:  # Saturday = 5, Sunday = 6
        day_name = date_value.strftime("%A")
        errors.append(ValidationError(
            field=field_name,
            message=f"{field_name} falls on a {day_name}",
            severity="warning",
            suggestion="Verify if weekend dates are intended for this calculation"
        ))
    
    return errors


def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> List[ValidationError]:
    """
    Validate that date range is logical and reasonable.
    
    Args:
        start_date: Start date to validate
        end_date: End date to validate
        
    Returns:
        List[ValidationError]: List of validation errors (empty if valid)
    """
    errors = []
    
    if start_date is None or end_date is None:
        return errors  # Individual date validation will catch missing dates
    
    # Check that start date is before end date
    if start_date >= end_date:
        errors.append(ValidationError(
            field="date_range",
            message="Start date must be before end date",
            severity="error",
            suggestion=f"Start: {start_date.strftime('%m/%d/%Y')}, End: {end_date.strftime('%m/%d/%Y')}"
        ))
        return errors
    
    # Calculate period length
    period_days = (end_date - start_date).days
    
    # Check for very short periods (less than 1 day)
    if period_days < 1:
        errors.append(ValidationError(
            field="date_range",
            message="Interest period is less than 1 day",
            severity="warning",
            suggestion="Verify if same-day or overnight interest calculation is intended"
        ))
    
    # Check for very long periods (more than 2 years)
    if period_days > 730:  # 2 years
        errors.append(ValidationError(
            field="date_range",
            message=f"Interest period is very long ({period_days} days)",
            severity="warning",
            suggestion="Verify if multi-year interest calculation is intended"
        ))
    
    # Check for periods longer than 10 years (likely error)
    if period_days > 3650:  # 10 years
        errors.append(ValidationError(
            field="date_range",
            message=f"Interest period is unreasonably long ({period_days} days)",
            severity="error",
            suggestion="Check if dates are correct - period exceeds 10 years"
        ))
    
    return errors


def validate_principal_amount(amount: Optional[float]) -> List[ValidationError]:
    """
    Validate principal amount for reasonableness and format.
    
    Args:
        amount: Principal amount to validate
        
    Returns:
        List[ValidationError]: List of validation errors (empty if valid)
    """
    errors = []
    
    if amount is None:
        errors.append(ValidationError(
            field="principal_amount",
            message="Principal amount is required",
            severity="error",
            suggestion="Ensure the PDF contains a clearly marked dollar amount (e.g., $1,234,567.89)"
        ))
        return errors
    
    # Check for positive amount
    if amount <= 0:
        errors.append(ValidationError(
            field="principal_amount",
            message="Principal amount must be positive",
            severity="error",
            suggestion=f"Found amount: ${amount:,.2f} - check if this is correct"
        ))
        return errors
    
    # Check for very small amounts (likely extraction error)
    if amount < 1000:  # Less than $1,000
        errors.append(ValidationError(
            field="principal_amount",
            message=f"Principal amount seems very small (${amount:,.2f})",
            severity="warning",
            suggestion="Verify if this is the correct principal amount or if extraction missed larger amount"
        ))
    
    # Check for very large amounts (over $1 billion)
    if amount > 1_000_000_000:  # Over $1 billion
        errors.append(ValidationError(
            field="principal_amount",
            message=f"Principal amount seems very large (${amount:,.2f})",
            severity="warning",
            suggestion="Verify if this is the correct principal amount"
        ))
    
    # Check for unreasonably large amounts (over $100 billion)
    if amount > 100_000_000_000:  # Over $100 billion
        errors.append(ValidationError(
            field="principal_amount",
            message=f"Principal amount is unreasonably large (${amount:,.2f})",
            severity="error",
            suggestion="Check if decimal point is in correct position"
        ))
    
    return errors


def validate_interest_rate(rate: Optional[float]) -> List[ValidationError]:
    """
    Validate interest rate for reasonableness and format.
    
    Args:
        rate: Interest rate as decimal (e.g., 0.05 for 5%)
        
    Returns:
        List[ValidationError]: List of validation errors (empty if valid)
    """
    errors = []
    
    if rate is None:
        errors.append(ValidationError(
            field="interest_rate",
            message="Interest rate is required",
            severity="error",
            suggestion="Ensure the PDF contains a clearly marked percentage (e.g., 5.25%)"
        ))
        return errors
    
    # Check for non-negative rate
    if rate < 0:
        errors.append(ValidationError(
            field="interest_rate",
            message="Interest rate cannot be negative",
            severity="error",
            suggestion=f"Found rate: {rate * 100:.4f}% - check if this is correct"
        ))
        return errors
    
    # Check for very low rates (below 0.01% - likely extraction error)
    if rate < 0.0001:  # Less than 0.01%
        errors.append(ValidationError(
            field="interest_rate",
            message=f"Interest rate seems very low ({rate * 100:.6f}%)",
            severity="warning",
            suggestion="Verify if this is the correct rate or if extraction missed decimal point"
        ))
    
    # Check for high but reasonable rates (above 25%)
    if rate > 0.25:  # Over 25%
        errors.append(ValidationError(
            field="interest_rate",
            message=f"Interest rate seems high ({rate * 100:.2f}%)",
            severity="warning",
            suggestion="Verify if this is the correct annual rate"
        ))
    
    # Check for unreasonably high rates (above 100%)
    if rate > 1.0:  # Over 100%
        errors.append(ValidationError(
            field="interest_rate",
            message=f"Interest rate is unreasonably high ({rate * 100:.2f}%)",
            severity="error",
            suggestion="Check if percentage was extracted as decimal (e.g., 5.25 instead of 0.0525)"
        ))
    
    return errors


def validate_interest_amount(amount: Optional[float], principal: Optional[float] = None) -> List[ValidationError]:
    """
    Validate interest amount for reasonableness.
    
    Args:
        amount: Interest amount to validate
        principal: Principal amount for comparison (optional)
        
    Returns:
        List[ValidationError]: List of validation errors (empty if valid)
    """
    errors = []
    
    if amount is None:
        errors.append(ValidationError(
            field="interest_amount",
            message="Interest amount is required",
            severity="error",
            suggestion="Ensure the PDF contains a clearly marked interest amount"
        ))
        return errors
    
    # Check for non-negative amount
    if amount < 0:
        errors.append(ValidationError(
            field="interest_amount",
            message="Interest amount cannot be negative",
            severity="error",
            suggestion=f"Found amount: ${amount:,.2f} - check if this is correct"
        ))
        return errors
    
    # Check for very small amounts (below $1)
    if amount < 1:
        errors.append(ValidationError(
            field="interest_amount",
            message=f"Interest amount seems very small (${amount:.2f})",
            severity="warning",
            suggestion="Verify if this is the correct interest amount"
        ))
    
    # Compare to principal if available
    if principal is not None and principal > 0:
        ratio = amount / principal
        
        # Interest should not exceed principal (100% of principal)
        if ratio > 1.0:
            errors.append(ValidationError(
                field="interest_amount",
                message=f"Interest amount (${amount:,.2f}) exceeds principal (${principal:,.2f})",
                severity="error",
                suggestion="Check if interest amount and principal are correctly identified"
            ))
        
        # Very high interest ratio (over 50% of principal)
        elif ratio > 0.5:
            errors.append(ValidationError(
                field="interest_amount",
                message=f"Interest amount is very high ({ratio * 100:.1f}% of principal)",
                severity="warning",
                suggestion="Verify if this represents a long-term or high-rate calculation"
            ))
    
    return errors


def validate_required_fields_completeness(extracted_data) -> List[ValidationError]:
    """
    Validate that all required fields are present and complete.
    
    Args:
        extracted_data: ExtractedData object to validate
        
    Returns:
        List[ValidationError]: List of validation errors (empty if all complete)
    """
    errors = []
    
    if extracted_data is None:
        errors.append(ValidationError(
            field="general",
            message="No data was extracted from the PDF",
            severity="error",
            suggestion="Ensure the PDF contains readable financial information"
        ))
        return errors
    
    # Check each required field
    required_fields = {
        'principal_amount': 'Principal amount',
        'interest_rate': 'Interest rate',
        'start_date': 'Start date',
        'end_date': 'End date',
        'notice_interest_amount': 'Interest amount'
    }
    
    missing_fields = []
    for field_name, display_name in required_fields.items():
        if getattr(extracted_data, field_name, None) is None:
            missing_fields.append(display_name)
    
    if missing_fields:
        errors.append(ValidationError(
            field="completeness",
            message=f"Missing required fields: {', '.join(missing_fields)}",
            severity="error",
            suggestion="Ensure the PDF contains all required financial information clearly marked"
        ))
    
    # Check extraction confidence if available
    if hasattr(extracted_data, 'extraction_confidence') and extracted_data.extraction_confidence:
        low_confidence_fields = []
        for field, confidence in extracted_data.extraction_confidence.items():
            if confidence < 0.5:  # Less than 50% confidence
                display_name = field.replace('_', ' ').title()
                low_confidence_fields.append(f"{display_name} ({confidence * 100:.0f}%)")
        
        if low_confidence_fields:
            errors.append(ValidationError(
                field="confidence",
                message=f"Low extraction confidence for: {', '.join(low_confidence_fields)}",
                severity="warning",
                suggestion="Review extracted values for accuracy"
            ))
    
    return errors


def perform_comprehensive_validation(extracted_data) -> ValidationResult:
    """
    Perform comprehensive validation of all extracted data.
    
    Args:
        extracted_data: ExtractedData object to validate
        
    Returns:
        ValidationResult: Comprehensive validation results
    """
    all_errors = []
    all_warnings = []
    validated_data = {}
    
    # Validate required fields completeness
    completeness_errors = validate_required_fields_completeness(extracted_data)
    all_errors.extend([e for e in completeness_errors if e.severity == "error"])
    all_warnings.extend([e for e in completeness_errors if e.severity == "warning"])
    
    if extracted_data is None:
        return ValidationResult(
            is_valid=False,
            errors=all_errors,
            warnings=all_warnings,
            validated_data=validated_data
        )
    
    # Validate individual fields
    principal_errors = validate_principal_amount(extracted_data.principal_amount)
    all_errors.extend([e for e in principal_errors if e.severity == "error"])
    all_warnings.extend([e for e in principal_errors if e.severity == "warning"])
    
    rate_errors = validate_interest_rate(extracted_data.interest_rate)
    all_errors.extend([e for e in rate_errors if e.severity == "error"])
    all_warnings.extend([e for e in rate_errors if e.severity == "warning"])
    
    start_date_errors = validate_date_format_and_range(extracted_data.start_date, "Start date")
    all_errors.extend([e for e in start_date_errors if e.severity == "error"])
    all_warnings.extend([e for e in start_date_errors if e.severity == "warning"])
    
    end_date_errors = validate_date_format_and_range(extracted_data.end_date, "End date")
    all_errors.extend([e for e in end_date_errors if e.severity == "error"])
    all_warnings.extend([e for e in end_date_errors if e.severity == "warning"])
    
    date_range_errors = validate_date_range(extracted_data.start_date, extracted_data.end_date)
    all_errors.extend([e for e in date_range_errors if e.severity == "error"])
    all_warnings.extend([e for e in date_range_errors if e.severity == "warning"])
    
    interest_errors = validate_interest_amount(
        extracted_data.notice_interest_amount, 
        extracted_data.principal_amount
    )
    all_errors.extend([e for e in interest_errors if e.severity == "error"])
    all_warnings.extend([e for e in interest_errors if e.severity == "warning"])
    
    # Store validated data (even if there are warnings)
    validated_data = {
        'principal_amount': extracted_data.principal_amount,
        'interest_rate': extracted_data.interest_rate,
        'start_date': extracted_data.start_date,
        'end_date': extracted_data.end_date,
        'notice_interest_amount': extracted_data.notice_interest_amount
    }
    
    # Determine overall validity (no errors, warnings are acceptable)
    is_valid = len(all_errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=all_errors,
        warnings=all_warnings,
        validated_data=validated_data
    )


def format_validation_errors_for_display(validation_result: ValidationResult) -> Dict[str, Any]:
    """
    Format validation errors for user-friendly display.
    
    Args:
        validation_result: ValidationResult object containing errors and warnings
        
    Returns:
        Dict[str, Any]: Formatted display information
    """
    display_info = {
        'has_errors': len(validation_result.errors) > 0,
        'has_warnings': len(validation_result.warnings) > 0,
        'error_count': len(validation_result.errors),
        'warning_count': len(validation_result.warnings),
        'errors': [],
        'warnings': [],
        'summary': ""
    }
    
    # Format errors
    for error in validation_result.errors:
        display_info['errors'].append({
            'field': error.field,
            'message': error.message,
            'suggestion': error.suggestion
        })
    
    # Format warnings
    for warning in validation_result.warnings:
        display_info['warnings'].append({
            'field': warning.field,
            'message': warning.message,
            'suggestion': warning.suggestion
        })
    
    # Create summary
    if display_info['has_errors']:
        display_info['summary'] = f"Found {display_info['error_count']} error(s)"
        if display_info['has_warnings']:
            display_info['summary'] += f" and {display_info['warning_count']} warning(s)"
    elif display_info['has_warnings']:
        display_info['summary'] = f"Found {display_info['warning_count']} warning(s)"
    else:
        display_info['summary'] = "All validations passed"
    
    return display_info