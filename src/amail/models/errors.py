"""Error response models for the email API."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response body with a human-readable message."""

    detail: str
