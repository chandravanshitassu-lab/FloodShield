"""
Standardised JSON response helpers.
Provides consistent envelope structure across all API endpoints.
"""
from __future__ import annotations
from typing import Any
from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JSONResponse:
    """Return a standard success response envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def created(data: Any = None, message: str = "Created successfully") -> JSONResponse:
    """Return an HTTP 201 Created response."""
    return success(data=data, message=message, status_code=201)


def error(message: str, status_code: int = 400, details: Any = None) -> JSONResponse:
    """Return a standard error response envelope."""
    content: dict[str, Any] = {"success": False, "error": message}
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)
