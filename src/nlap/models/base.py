"""Base data models for the application."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(default=False)
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_details: Optional[dict] = Field(default=None, description="Error details")


class HealthCheckResponse(BaseResponse):
    """Health check response model."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    components: dict[str, dict] = Field(default_factory=dict, description="Component health status")

