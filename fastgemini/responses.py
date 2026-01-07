"""
Response helpers and factory functions.
"""

from fastgemini.enums import GEMINI_MEDIA_TYPE, Status
from fastgemini.schema import GeminiResponse


def success(
    body: str,
    content_type: str = GEMINI_MEDIA_TYPE,
) -> GeminiResponse:
    """Create a successful response with body content."""
    return GeminiResponse(
        status=Status.SUCCESS,
        content_type=content_type,
        body=body,
    )


def redirect(
    url: str,
    permanent: bool = False,
) -> GeminiResponse:
    """Create a redirect response."""
    return GeminiResponse(
        status=Status.REDIRECT_PERMANENT if permanent else Status.REDIRECT_TEMPORARY,
        content_type=url,
    )


def not_found(message: str = "Resource not found") -> GeminiResponse:
    """Create a not found response."""
    return GeminiResponse(
        status=Status.NOT_FOUND,
        content_type=message,
    )


def input_required(prompt: str, sensitive: bool = False) -> GeminiResponse:
    """Create an input request response."""
    return GeminiResponse(
        status=Status.SENSITIVE_INPUT if sensitive else Status.INPUT,
        content_type=prompt,
    )


def error(
    message: str = "Server error",
    status: Status = Status.TEMPORARY_FAILURE,
) -> GeminiResponse:
    """Create an error response."""
    return GeminiResponse(
        status=status,
        content_type=message,
    )


def certificate_required(message: str = "Client certificate required") -> GeminiResponse:
    """Create a certificate required response."""
    return GeminiResponse(
        status=Status.CLIENT_CERTIFICATE_REQUIRED,
        content_type=message,
    )
