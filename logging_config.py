"""
Comprehensive Logging Configuration for LoanGuard Interest Validator

This module provides centralized logging configuration for debugging and monitoring
the LoanGuard application. It includes structured logging with different levels
for various components and operations.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
import json


class LoanGuardFormatter(logging.Formatter):
    """Custom formatter for LoanGuard logging with structured output."""
    
    def format(self, record):
        """Format log record with structured information."""
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_session'):
            log_entry['user_session'] = record.user_session
        if hasattr(record, 'loan_file_name'):
            log_entry['file_name'] = record.loan_file_name
        if hasattr(record, 'loan_operation'):
            log_entry['operation'] = record.loan_operation
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'validation_status'):
            log_entry['validation_status'] = record.validation_status
        
        # Format as JSON for structured logging
        return json.dumps(log_entry, default=str)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up comprehensive logging configuration for LoanGuard.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('loanguard')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = LoanGuardFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler (10MB max, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = 'loanguard') -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class LoggingContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        # Temporarily disable custom logging context to avoid LogRecord conflicts
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # No-op for now
        pass


def log_operation(operation_name: str):
    """
    Decorator for logging function operations with timing.
    
    Args:
        operation_name: Name of the operation being logged
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = datetime.now()
            
            try:
                with LoggingContext(logger, loan_operation=operation_name):
                    logger.info(f"Starting operation: {operation_name}")
                    result = func(*args, **kwargs)
                    
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(
                        f"Operation completed successfully: {operation_name}",
                        extra={'duration_ms': duration}
                    )
                    return result
                    
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Operation failed: {operation_name} - {str(e)}",
                    extra={
                        'duration_ms': duration,
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_validation_result(validation_result, file_name: str = None):
    """
    Log validation results with structured information.
    
    Args:
        validation_result: ValidationResult object
        file_name: Name of the processed file
    """
    logger = get_logger()
    
    extra_info = {
        'operation': 'validation',
        'validation_status': validation_result.status,
        'difference_amount': validation_result.difference_amount,
        'tolerance_used': validation_result.tolerance_used
    }
    
    if file_name:
        extra_info['loan_file_name'] = file_name
    
    logger.info(
        f"Validation {validation_result.status} - difference: ${validation_result.difference_amount:.2f}"
    )


def log_extraction_result(extracted_data, file_name: str = None):
    """
    Log data extraction results with structured information.
    
    Args:
        extracted_data: ExtractedData object
        file_name: Name of the processed file
    """
    logger = get_logger()
    
    # Count extracted fields
    fields_extracted = sum(1 for field in [
        extracted_data.principal_amount,
        extracted_data.interest_rate,
        extracted_data.start_date,
        extracted_data.end_date,
        extracted_data.notice_interest_amount
    ] if field is not None)
    
    extra_info = {
        'operation': 'extraction',
        'fields_extracted': fields_extracted,
        'total_fields': 5
    }
    
    if file_name:
        extra_info['loan_file_name'] = file_name
    
    if hasattr(extracted_data, 'extraction_confidence'):
        avg_confidence = sum(extracted_data.extraction_confidence.values()) / len(extracted_data.extraction_confidence)
        extra_info['avg_confidence'] = avg_confidence
    
    logger.info(
        f"Data extraction completed - {fields_extracted}/5 fields extracted"
    )


def log_calculation_result(calculation_result, file_name: str = None):
    """
    Log interest calculation results with structured information.
    
    Args:
        calculation_result: CalculationResult object
        file_name: Name of the processed file
    """
    logger = get_logger()
    
    extra_info = {
        'operation': 'calculation',
        'expected_interest': calculation_result.expected_interest,
        'days_calculated': calculation_result.days_calculated
    }
    
    if file_name:
        extra_info['loan_file_name'] = file_name
    
    logger.info(
        f"Interest calculation completed - amount: ${calculation_result.expected_interest:.2f}"
    )


def log_error(error: Exception, operation: str, file_name: str = None, **context):
    """
    Log errors with structured information and context.
    
    Args:
        error: Exception that occurred
        operation: Operation that was being performed
        file_name: Name of the file being processed (if applicable)
        **context: Additional context information
    """
    logger = get_logger()
    
    extra_info = {
        'operation_name': operation,
        'error_type': type(error).__name__,
        **context
    }
    
    if file_name:
        extra_info['loan_file_name'] = file_name
    
    logger.error(
        f"Error in {operation}: {str(error)}",
        exc_info=True
    )


# Initialize default logger
default_logger = setup_logging()