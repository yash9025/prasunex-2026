"""Application exception classes and response models.

Enforces standardized JSON error envelopes across all endpoints:
{
    "code": "ERROR_CODE",
    "message": "Human readable error description",
    "request_id": "req-uuid",
    "details": { ... }
}
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error envelope per Section 7.2 of the specification."""

    code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Teacher-facing or developer-safe error message")
    request_id: Optional[str] = Field(None, description="Unique correlation request ID")
    details: Optional[Dict[str, Any]] = Field(None, description="Safe contextual metadata")


class AppException(HTTPException):
    """Base application exception with standardized code and details."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class AuthenticationError(AppException):
    """Raised on missing or invalid JWT tokens (401)."""

    def __init__(self, message: str = "Authentication required or token expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
        )


class AuthorizationError(AppException):
    """Raised when an authenticated actor lacks tenant or class permission (403)."""

    def __init__(self, message: str = "Access denied for the requested resource or school"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN_RESOURCE",
            message=message,
        )


class ResourceNotFoundError(AppException):
    """Raised when a resource does not exist or is in another tenant (404)."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found or inaccessible.",
        )


class ConflictError(AppException):
    """Raised on optimistic locking conflicts or idempotency mismatches (409)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=message,
            details=details,
        )


class PayloadTooLargeError(AppException):
    """Raised when upload size exceeds bounds (413)."""

    def __init__(self, message: str = "Payload exceeds maximum allowed size"):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="PAYLOAD_TOO_LARGE",
            message=message,
        )


class ValidationError(AppException):
    """Raised on invalid CSV format or schema failure (422)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message=message,
            details=details,
        )
