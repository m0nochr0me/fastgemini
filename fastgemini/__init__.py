"""
FastAPI-style Gemini Protocol Framework
"""

from fastgemini.app import GeminiApp
from fastgemini.responses import (
    certificate_required,
    error,
    input_required,
    not_found,
    redirect,
    success,
)
from fastgemini.router import GeminiRouter

__version__ = "0.1.0"

__all__ = (
    "GeminiApp",
    "GeminiRouter",
    "certificate_required",
    "error",
    "input_required",
    "not_found",
    "redirect",
    "success",
)
