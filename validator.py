"""
Validation and Comparison Module

This module implements validation logic for comparing calculated interest amounts
against notice interest amounts. It provides tolerance calculations, comparison
logic, and clear pass/fail messaging for banking-grade validation.
"""

from dataclasses import dataclass
from typing import Optional
from calculator import CalculationResult
from extractor import ExtractedData


@dataclass
class ValidationResult:
    """Data class to hold validation results and detailed explanations."""
    status: str  # "PASS" or "FAIL"
    difference_amount: float
    percentage_difference: float
    message: str
    detailed_explanation: str
    tolerance_used: float
    expected_amount: float
    notice_amount: float


def calculate_tolerance(amount: float) -> float:
    """
    Calculate acceptable tolerance for interest amount comparison.
    
    Uses the larger of $1.00 or 0.01% of the amount as tolerance,
    following standard banking practices for interest validation.
    
    Args:
        amount: Interest amount to calculate tolerance for
        
    Returns:
        float: Tolerance amount in dollars
    """
    if amount <= 0:
        return 1.0  # Minimum $1 tolerance for edge cases
    
    # Calculate 0.01% of amount (1 basis point)
    percentage_tolerance = amount * 0.0001
    
    # Return the larger of $1 or 0.01%
    return max(1.0, percentage_tolerance)


def validate_interest_calculation(extracted_data: ExtractedData, calculation_result: CalculationResult) -> ValidationResult:
    """
    Compare calculated vs reported interest amounts and determine pass/fail status.
    
    Args:
        extracted_data: ExtractedData object containing notice interest amount
        calculation_result: CalculationResult object containing calculated interest
        
    Returns:
        ValidationResult: Object containing validation status and detailed explanations
        
    Raises:
        ValueError: If required data is missing for validation
    """
    # Validate inputs
    if calculation_result is None or calculation_result.expected_interest is None:
        raise ValueError("Calculation result is required for validation")
    
    if extracted_data is None or extracted_data.notice_interest_amount is None:
        raise ValueError("Notice interest amount is required for validation")
    
    expected = calculation_result.expected_interest
    notice = extracted_data.notice_interest_amount
    
    # Calculate difference metrics
    difference = abs(expected - notice)
    percentage_diff = (difference / expected * 100) if expected > 0 else 0
    
    # Calculate tolerance
    tolerance = calculate_tolerance(expected)
    
    # Determine validation status
    if difference <= tolerance:
        # PASS result
        status = "PASS"
        message = "Notice is Correct"
        detailed_explanation = (
            f"The interest calculation in the notice matches our expected calculation "
            f"within acceptable tolerance. The difference of ${difference:.2f} is within "
            f"the acceptable tolerance of ${tolerance:.2f}."
        )
    else:
        # FAIL result
        status = "FAIL"
        message = "Issue Detected"
        
        if notice > expected:
            direction = "more"
            detailed_explanation = (
                f"The notice shows ${difference:.2f} more than expected. "
                f"This difference of ${difference:.2f} exceeds the acceptable tolerance "
                f"of ${tolerance:.2f}. Please review the interest calculation in the notice."
            )
        else:
            direction = "less"
            detailed_explanation = (
                f"The notice shows ${difference:.2f} less than expected. "
                f"This difference of ${difference:.2f} exceeds the acceptable tolerance "
                f"of ${tolerance:.2f}. Please review the interest calculation in the notice."
            )
    
    return ValidationResult(
        status=status,
        difference_amount=difference,
        percentage_difference=percentage_diff,
        message=message,
        detailed_explanation=detailed_explanation,
        tolerance_used=tolerance,
        expected_amount=expected,
        notice_amount=notice
    )


def generate_validation_summary(validation_result: ValidationResult) -> str:
    """
    Generate a comprehensive validation summary for display.
    
    Args:
        validation_result: ValidationResult object containing validation details
        
    Returns:
        str: Formatted summary text for user display
    """
    summary_lines = []
    
    # Status header
    if validation_result.status == "PASS":
        summary_lines.append("✅ VALIDATION PASSED")
        summary_lines.append("The interest notice calculation is correct.")
    else:
        summary_lines.append("❌ VALIDATION FAILED")
        summary_lines.append("The interest notice calculation contains an error.")
    
    # Amount comparison
    summary_lines.append("")
    summary_lines.append("AMOUNT COMPARISON:")
    summary_lines.append(f"Expected (Calculated): ${validation_result.expected_amount:,.2f}")
    summary_lines.append(f"Notice (PDF):         ${validation_result.notice_amount:,.2f}")
    summary_lines.append(f"Difference:           ${validation_result.difference_amount:,.2f}")
    summary_lines.append(f"Percentage Diff:      {validation_result.percentage_difference:.2f}%")
    summary_lines.append(f"Tolerance Used:       ${validation_result.tolerance_used:,.2f}")
    
    # Detailed explanation
    summary_lines.append("")
    summary_lines.append("EXPLANATION:")
    summary_lines.append(validation_result.detailed_explanation)
    
    return "\n".join(summary_lines)


def get_validation_recommendations(validation_result: ValidationResult) -> list[str]:
    """
    Generate actionable recommendations based on validation results.
    
    Args:
        validation_result: ValidationResult object containing validation details
        
    Returns:
        list[str]: List of recommendation strings
    """
    recommendations = []
    
    if validation_result.status == "PASS":
        recommendations.extend([
            "The notice is ready to be sent to lenders",
            "No further action required for this interest calculation",
            "Consider archiving this validation result for audit purposes"
        ])
    else:
        recommendations.extend([
            "Review the interest calculation in the notice before sending",
            "Verify that the principal amount, interest rate, and dates are correct",
            "Check for any special terms or adjustments that might affect the calculation",
            "Consider recalculating the interest using the extracted data"
        ])
        
        # Add specific recommendations based on difference magnitude
        if validation_result.percentage_difference > 5.0:
            recommendations.append("The difference is significant (>5%) - double-check all input values")
        elif validation_result.percentage_difference > 1.0:
            recommendations.append("The difference is moderate (>1%) - review calculation methodology")
        
        # Add recommendations based on direction of error
        if validation_result.notice_amount > validation_result.expected_amount:
            recommendations.append("The notice amount is higher than expected - check for additional fees or adjustments")
        else:
            recommendations.append("The notice amount is lower than expected - check for missing interest components")
    
    return recommendations


def format_validation_for_display(validation_result: ValidationResult) -> dict:
    """
    Format validation result for UI display with proper styling information.
    
    Args:
        validation_result: ValidationResult object containing validation details
        
    Returns:
        dict: Dictionary containing formatted display information
    """
    if validation_result.status == "PASS":
        return {
            "status_color": "success",
            "status_icon": "🟢",
            "status_text": "PASS",
            "status_message": validation_result.message,
            "card_style": "success",
            "explanation": validation_result.detailed_explanation,
            "recommendations": get_validation_recommendations(validation_result)
        }
    else:
        return {
            "status_color": "error",
            "status_icon": "🔴",
            "status_text": "FAIL",
            "status_message": validation_result.message,
            "card_style": "error",
            "explanation": validation_result.detailed_explanation,
            "recommendations": get_validation_recommendations(validation_result)
        }


def validate_extracted_data_completeness(extracted_data: ExtractedData) -> dict[str, str]:
    """
    Validate that extracted data contains all required fields for validation.
    
    Args:
        extracted_data: ExtractedData object to validate
        
    Returns:
        dict[str, str]: Dictionary of field names to error messages (empty if all valid)
    """
    errors = {}
    
    if extracted_data is None:
        errors['general'] = "No extracted data available"
        return errors
    
    # Check required fields
    if extracted_data.principal_amount is None:
        errors['principal'] = "Principal amount not found in PDF"
    elif extracted_data.principal_amount <= 0:
        errors['principal'] = "Principal amount must be positive"
    
    if extracted_data.interest_rate is None:
        errors['rate'] = "Interest rate not found in PDF"
    elif extracted_data.interest_rate < 0:
        errors['rate'] = "Interest rate cannot be negative"
    
    if extracted_data.start_date is None:
        errors['start_date'] = "Start date not found in PDF"
    
    if extracted_data.end_date is None:
        errors['end_date'] = "End date not found in PDF"
    
    if extracted_data.start_date and extracted_data.end_date:
        if extracted_data.start_date >= extracted_data.end_date:
            errors['date_range'] = "Start date must be before end date"
    
    if extracted_data.notice_interest_amount is None:
        errors['notice_amount'] = "Interest amount not found in PDF notice"
    elif extracted_data.notice_interest_amount < 0:
        errors['notice_amount'] = "Interest amount cannot be negative"
    
    return errors


def can_perform_validation(extracted_data: ExtractedData, calculation_result: CalculationResult) -> tuple[bool, list[str]]:
    """
    Check if validation can be performed with the available data.
    
    Args:
        extracted_data: ExtractedData object containing extracted information
        calculation_result: CalculationResult object containing calculated interest
        
    Returns:
        tuple[bool, list[str]]: (can_validate, list_of_issues)
    """
    issues = []
    
    # Check extracted data
    data_errors = validate_extracted_data_completeness(extracted_data)
    if data_errors:
        issues.extend([f"Data extraction issue: {error}" for error in data_errors.values()])
    
    # Check calculation result
    if calculation_result is None:
        issues.append("Interest calculation not available")
    elif calculation_result.expected_interest is None:
        issues.append("Calculated interest amount not available")
    elif calculation_result.expected_interest < 0:
        issues.append("Calculated interest amount is invalid")
    
    can_validate = len(issues) == 0
    return can_validate, issues