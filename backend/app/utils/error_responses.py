"""Standardized error response system with user-friendly messages"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

from app.core.logging import logger


class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Photograph quality errors (E001-E099)
    E001 = "E001"  # No face detected
    E002 = "E002"  # Multiple faces detected
    E003 = "E003"  # Image quality too low (blur/lighting)
    E004 = "E004"  # Face too small or occluded
    E005 = "E005"  # Invalid image format
    E006 = "E006"  # Image file too large
    E007 = "E007"  # Image resolution too low
    
    # Processing errors (E100-E199)
    E100 = "E100"  # Face detection failed
    E101 = "E101"  # Embedding generation failed
    E102 = "E102"  # Duplicate detection failed
    E103 = "E103"  # Identity creation failed
    E104 = "E104"  # Processing timeout
    E105 = "E105"  # Queue full
    
    # Database errors (E200-E299)
    E200 = "E200"  # Database connection failed
    E201 = "E201"  # Database query failed
    E202 = "E202"  # Record not found
    E203 = "E203"  # Duplicate record
    
    # Authentication/Authorization errors (E300-E399)
    E300 = "E300"  # Authentication failed
    E301 = "E301"  # Invalid credentials
    E302 = "E302"  # Token expired
    E303 = "E303"  # Insufficient permissions
    E304 = "E304"  # Account suspended
    
    # Validation errors (E400-E499)
    E400 = "E400"  # Invalid request data
    E401 = "E401"  # Missing required field
    E402 = "E402"  # Invalid field format
    E403 = "E403"  # Field value out of range
    
    # System errors (E500-E599)
    E500 = "E500"  # Internal server error
    E501 = "E501"  # Service unavailable
    E502 = "E502"  # External service error
    E503 = "E503"  # Circuit breaker open
    E504 = "E504"  # Rate limit exceeded


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"  # User can retry immediately
    MEDIUM = "medium"  # User should wait before retry
    HIGH = "high"  # User action required
    CRITICAL = "critical"  # System intervention required


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error_code: str
    message: str
    user_message: str
    severity: ErrorSeverity
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    actionable_feedback: Optional[List[str]] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry
    support_reference: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON-serializable datetime"""
        data = self.model_dump()
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ErrorMessageMapper:
    """Maps internal errors to user-friendly messages"""
    
    # Error code to message mapping
    ERROR_MESSAGES = {
        # Photograph quality errors
        ErrorCode.E001: {
            "message": "No face detected in photograph",
            "user_message": "We couldn't detect a face in your photograph. Please submit a clear photo showing your face.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Ensure your face is clearly visible in the photograph",
                "Use good lighting and face the camera directly",
                "Remove any obstructions (sunglasses, masks, etc.)",
                "Make sure the photograph is not blurry"
            ]
        },
        ErrorCode.E002: {
            "message": "Multiple faces detected in photograph",
            "user_message": "Your photograph contains multiple faces. Please submit a photo with only your face.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Take a photograph with only yourself in the frame",
                "Ensure no other people are visible in the background",
                "Use a plain background if possible"
            ]
        },
        ErrorCode.E003: {
            "message": "Photograph quality too low",
            "user_message": "The quality of your photograph is too low. Please submit a clearer, higher-quality image.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Use a camera with better resolution",
                "Ensure good lighting (natural light works best)",
                "Keep the camera steady to avoid blur",
                "Clean your camera lens before taking the photo",
                "Avoid using heavily compressed or edited images"
            ]
        },
        ErrorCode.E004: {
            "message": "Face too small or occluded",
            "user_message": "Your face appears too small or partially hidden. Please submit a closer, clearer photograph.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Move closer to the camera or zoom in",
                "Ensure your entire face is visible",
                "Remove any obstructions (hair, hands, objects)",
                "Face should occupy at least 50% of the image"
            ]
        },
        ErrorCode.E005: {
            "message": "Invalid image format",
            "user_message": "The image format is not supported. Please upload a JPEG or PNG file.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Convert your image to JPEG or PNG format",
                "Ensure the file is not corrupted",
                "Try taking a new photograph"
            ]
        },
        ErrorCode.E006: {
            "message": "Image file too large",
            "user_message": "Your image file is too large. Please upload an image smaller than 10MB.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Compress the image file",
                "Reduce image resolution if very high",
                "Use JPEG format for smaller file size"
            ]
        },
        ErrorCode.E007: {
            "message": "Image resolution too low",
            "user_message": "Your image resolution is too low. Please upload an image with at least 300x300 pixels.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Use a higher resolution camera",
                "Ensure image is at least 300x300 pixels",
                "Avoid using thumbnail or preview images"
            ]
        },
        
        # Processing errors
        ErrorCode.E100: {
            "message": "Face detection processing failed",
            "user_message": "We encountered an error while processing your photograph. Please try again.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Wait a moment and try submitting again",
                "If the problem persists, try a different photograph",
                "Contact support if the issue continues"
            ]
        },
        ErrorCode.E101: {
            "message": "Embedding generation failed",
            "user_message": "We couldn't process your facial features. Please try again with a different photograph.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Try submitting a different photograph",
                "Ensure the photograph meets quality requirements",
                "Contact support if the issue persists"
            ]
        },
        ErrorCode.E102: {
            "message": "Duplicate detection failed",
            "user_message": "We encountered an error while checking for duplicates. Please try again later.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Wait a few minutes and try again",
                "Your application has been saved and will be processed",
                "Contact support if you need immediate assistance"
            ]
        },
        ErrorCode.E104: {
            "message": "Processing timeout",
            "user_message": "Your application is taking longer than expected to process. Please check back later.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Check your application status in 5-10 minutes",
                "Your application is still being processed",
                "Contact support if status doesn't update within 1 hour"
            ]
        },
        ErrorCode.E105: {
            "message": "Processing queue full",
            "user_message": "We're experiencing high volume. Please try submitting your application again in a few minutes.",
            "severity": ErrorSeverity.MEDIUM,
            "retry_after": 300,  # 5 minutes
            "actionable_feedback": [
                "Wait 5 minutes before trying again",
                "Try during off-peak hours for faster processing",
                "Your application was not saved, please resubmit"
            ]
        },
        
        # Database errors
        ErrorCode.E200: {
            "message": "Database connection failed",
            "user_message": "We're experiencing technical difficulties. Please try again later.",
            "severity": ErrorSeverity.HIGH,
            "retry_after": 60,
            "actionable_feedback": [
                "Wait a minute and try again",
                "Contact support if the issue persists"
            ]
        },
        ErrorCode.E202: {
            "message": "Record not found",
            "user_message": "The requested application was not found. Please check your application ID.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Verify your application ID is correct",
                "Check if you received a confirmation email",
                "Contact support with your details"
            ]
        },
        
        # Authentication errors
        ErrorCode.E300: {
            "message": "Authentication failed",
            "user_message": "Authentication failed. Please log in again.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Log in with your credentials",
                "Reset your password if you've forgotten it",
                "Contact support if you can't access your account"
            ]
        },
        ErrorCode.E301: {
            "message": "Invalid credentials",
            "user_message": "The username or password you entered is incorrect.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Check your username and password",
                "Ensure caps lock is not enabled",
                "Use the 'Forgot Password' option if needed"
            ]
        },
        ErrorCode.E302: {
            "message": "Token expired",
            "user_message": "Your session has expired. Please log in again.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Log in again to continue",
                "Your data has been saved"
            ]
        },
        ErrorCode.E303: {
            "message": "Insufficient permissions",
            "user_message": "You don't have permission to perform this action.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": [
                "Contact your administrator for access",
                "Verify you're using the correct account"
            ]
        },
        
        # Validation errors
        ErrorCode.E400: {
            "message": "Invalid request data",
            "user_message": "The information you provided is invalid. Please check and try again.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Review all required fields",
                "Ensure all information is correct",
                "Check for any error messages on the form"
            ]
        },
        ErrorCode.E401: {
            "message": "Missing required field",
            "user_message": "Some required information is missing. Please complete all required fields.",
            "severity": ErrorSeverity.LOW,
            "actionable_feedback": [
                "Fill in all fields marked as required",
                "Check for any highlighted fields"
            ]
        },
        
        # System errors
        ErrorCode.E500: {
            "message": "Internal server error",
            "user_message": "We encountered an unexpected error. Our team has been notified.",
            "severity": ErrorSeverity.CRITICAL,
            "actionable_feedback": [
                "Try again in a few minutes",
                "Contact support if the issue persists",
                "Reference the support ID when contacting us"
            ]
        },
        ErrorCode.E501: {
            "message": "Service unavailable",
            "user_message": "The service is temporarily unavailable. Please try again later.",
            "severity": ErrorSeverity.HIGH,
            "retry_after": 300,
            "actionable_feedback": [
                "Wait a few minutes and try again",
                "Check our status page for updates",
                "Contact support if urgent"
            ]
        },
        ErrorCode.E503: {
            "message": "Circuit breaker open - service unavailable",
            "user_message": "The service is temporarily unavailable due to technical issues. Please try again in a few minutes.",
            "severity": ErrorSeverity.HIGH,
            "retry_after": 60,
            "actionable_feedback": [
                "Wait at least 1 minute before trying again",
                "The service will automatically recover",
                "Contact support if the issue persists"
            ]
        },
        ErrorCode.E504: {
            "message": "Rate limit exceeded",
            "user_message": "You've made too many requests. Please wait before trying again.",
            "severity": ErrorSeverity.MEDIUM,
            "retry_after": 60,
            "actionable_feedback": [
                "Wait 1 minute before making another request",
                "Reduce the frequency of your requests"
            ]
        }
    }
    
    @classmethod
    def create_error_response(
        cls,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        support_reference: Optional[str] = None
    ) -> ErrorResponse:
        """
        Create standardized error response
        
        Args:
            error_code: Error code
            details: Optional additional details
            support_reference: Optional support reference ID
            
        Returns:
            ErrorResponse object
        """
        error_info = cls.ERROR_MESSAGES.get(error_code, {
            "message": "Unknown error",
            "user_message": "An unexpected error occurred. Please try again.",
            "severity": ErrorSeverity.MEDIUM,
            "actionable_feedback": ["Try again later", "Contact support if the issue persists"]
        })
        
        return ErrorResponse(
            error_code=error_code.value,
            message=error_info["message"],
            user_message=error_info["user_message"],
            severity=error_info["severity"],
            timestamp=datetime.utcnow(),
            details=details,
            actionable_feedback=error_info.get("actionable_feedback"),
            retry_after=error_info.get("retry_after"),
            support_reference=support_reference
        )
    
    @classmethod
    def map_exception_to_error_code(cls, exception: Exception) -> ErrorCode:
        """
        Map exception to appropriate error code
        
        Args:
            exception: Exception instance
            
        Returns:
            Appropriate error code
        """
        exception_name = type(exception).__name__
        exception_message = str(exception).lower()
        
        # Map common exceptions - check more specific patterns first
        if "no face" in exception_message and "detect" in exception_message:
            return ErrorCode.E001
        elif "multiple" in exception_message and "face" in exception_message:
            return ErrorCode.E002
        elif "blur" in exception_message or ("quality" in exception_message and "low" in exception_message):
            return ErrorCode.E003
        elif "small" in exception_message or "occluded" in exception_message:
            return ErrorCode.E004
        elif "format" in exception_message or "invalid" in exception_message:
            return ErrorCode.E005
        elif "timeout" in exception_message:
            return ErrorCode.E104
        elif "database" in exception_message or "connection" in exception_message:
            return ErrorCode.E200
        elif "not found" in exception_message:
            return ErrorCode.E202
        elif "authentication" in exception_message or "unauthorized" in exception_message:
            return ErrorCode.E300
        elif "permission" in exception_message or "forbidden" in exception_message:
            return ErrorCode.E303
        elif "circuit breaker" in exception_message:
            return ErrorCode.E503
        elif "rate limit" in exception_message:
            return ErrorCode.E504
        else:
            return ErrorCode.E500


def create_error_response(
    error_code: ErrorCode,
    details: Optional[Dict[str, Any]] = None,
    support_reference: Optional[str] = None
) -> ErrorResponse:
    """
    Convenience function to create error response
    
    Args:
        error_code: Error code
        details: Optional additional details
        support_reference: Optional support reference ID
        
    Returns:
        ErrorResponse object
    """
    return ErrorMessageMapper.create_error_response(error_code, details, support_reference)


def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    support_reference: Optional[str] = None
) -> ErrorResponse:
    """
    Handle exception and create appropriate error response
    
    Args:
        exception: Exception to handle
        context: Optional context information
        support_reference: Optional support reference ID
        
    Returns:
        ErrorResponse object
    """
    # Map exception to error code
    error_code = ErrorMessageMapper.map_exception_to_error_code(exception)
    
    # Create details
    details = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception)
    }
    
    if context:
        details["context"] = context
    
    # Log the error
    logger.error(
        f"Error handled: {error_code.value} - {str(exception)}",
        extra={"error_code": error_code.value, "context": context}
    )
    
    # Create and return error response
    return create_error_response(error_code, details, support_reference)
