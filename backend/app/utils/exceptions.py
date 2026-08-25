"""
Custom exception classes and global FastAPI exception handlers.
Register these handlers in main.py via app.add_exception_handler().
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class FloodShieldException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(FloodShieldException):
    def __init__(self, resource: str = "Resource", resource_id: int | str = "") -> None:
        super().__init__(
            message=f"{resource} with id={resource_id!r} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(FloodShieldException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class UnauthorizedError(FloodShieldException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(FloodShieldException):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


# ── Global Handlers ────────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(FloodShieldException)
    async def floodshield_exception_handler(
        request: Request, exc: FloodShieldException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Validation failed", "details": errors},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected internal server error occurred."},
        )
