"""
Custom exception hierarchy for the bank statement processor.

This module defines a comprehensive set of exceptions that provide
clear error categorization and better error handling throughout the application.
"""

from typing import Optional, Any, Dict


class StatementProcessingError(Exception):
    """
    Base exception for all statement processing errors.

    This is the root exception that all other custom exceptions inherit from,
    allowing for catch-all error handling when needed.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional structured data about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause),
            }

        return result


class ConfigurationError(StatementProcessingError):
    """
    Raised when there are configuration-related errors.

    Examples:
    - Missing API keys
    - Invalid configuration values
    - Missing required directories
    """

    pass


class PDFProcessingError(StatementProcessingError):
    """
    Base exception for PDF-related processing errors.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize PDF processing error.

        Args:
            message: Error message
            file_path: Path to the problematic PDF file
            details: Additional error details
            cause: Underlying exception
        """
        super().__init__(message, details, cause)
        self.file_path = file_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.file_path:
            result["file_path"] = self.file_path
        return result


class PDFExtractionError(PDFProcessingError):
    """
    Raised when PDF text extraction fails.

    Examples:
    - Corrupted PDF files
    - Password-protected PDFs
    - Unsupported PDF formats
    """

    pass


class PDFValidationError(PDFProcessingError):
    """
    Raised when PDF validation fails.

    Examples:
    - File is not a valid PDF
    - PDF is empty or has no extractable text
    - File size exceeds limits
    """

    pass


class AIProcessingError(StatementProcessingError):
    """
    Base exception for AI/LLM-related processing errors.
    """

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        prompt_length: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize AI processing error.

        Args:
            message: Error message
            model_name: Name of the AI model used
            prompt_length: Length of the prompt sent to the model
            details: Additional error details
            cause: Underlying exception
        """
        super().__init__(message, details, cause)
        self.model_name = model_name
        self.prompt_length = prompt_length

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.model_name:
            result["model_name"] = self.model_name
        if self.prompt_length:
            result["prompt_length"] = self.prompt_length
        return result


class AIConnectionError(AIProcessingError):
    """
    Raised when AI API connection fails.

    Examples:
    - Network connectivity issues
    - Invalid API keys
    - API service unavailable
    - Rate limiting
    """

    pass


class AIParsingError(AIProcessingError):
    """
    Raised when AI response parsing fails.

    Examples:
    - Invalid JSON in response
    - Missing required fields in response
    - Unexpected response format
    """

    def __init__(
        self,
        message: str,
        raw_response: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize AI parsing error.

        Args:
            message: Error message
            raw_response: Raw response from AI model
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.raw_response:
            # Truncate response for logging to avoid excessive log sizes
            truncated_response = (
                self.raw_response[:500] + "..."
                if len(self.raw_response) > 500
                else self.raw_response
            )
            result["raw_response_preview"] = truncated_response
            result["response_length"] = len(self.raw_response)
        return result


class DataValidationError(StatementProcessingError):
    """
    Raised when data validation fails.

    Examples:
    - Pydantic validation errors
    - Invalid transaction data
    - Missing required fields
    """

    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        invalid_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize data validation error.

        Args:
            message: Error message
            validation_errors: List of validation error details
            invalid_data: The data that failed validation
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []
        self.invalid_data = invalid_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.validation_errors:
            result["validation_errors"] = self.validation_errors
        if self.invalid_data:
            # Sanitize sensitive data for logging
            sanitized_data = self._sanitize_data(self.invalid_data)
            result["invalid_data_sample"] = sanitized_data
        return result

    @staticmethod
    def _sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from data for logging."""
        sensitive_fields = {'account_number', 'sort_code', 'api_key'}
        sanitized = {}

        for key, value in data.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = DataValidationError._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized


class StorageError(StatementProcessingError):
    """
    Raised when data storage operations fail.

    Examples:
    - CSV write failures
    - Disk space issues
    - Permission problems
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize storage error.

        Args:
            message: Error message
            file_path: Path to the file involved in the operation
            operation: Type of storage operation (read, write, append, etc.)
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.file_path:
            result["file_path"] = self.file_path
        if self.operation:
            result["storage_operation"] = self.operation
        return result


class DuplicationError(StatementProcessingError):
    """
    Raised when transaction deduplication issues occur.

    Examples:
    - Hash collision detection
    - Duplicate processing attempts
    """

    def __init__(
        self,
        message: str,
        transaction_hash: Optional[str] = None,
        duplicate_count: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize duplication error.

        Args:
            message: Error message
            transaction_hash: Hash of the duplicate transaction
            duplicate_count: Number of duplicates found
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.transaction_hash = transaction_hash
        self.duplicate_count = duplicate_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        if self.transaction_hash:
            result["transaction_hash"] = self.transaction_hash
        if self.duplicate_count:
            result["duplicate_count"] = self.duplicate_count
        return result