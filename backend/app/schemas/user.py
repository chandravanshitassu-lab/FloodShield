"""Pydantic v2 schemas for User API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.models.user import UserRole


# ── Request Schemas ────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, examples=["Ravi Kumar"])
    email: EmailStr = Field(..., examples=["ravi@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["SecureP@ss1"])
    phone: str | None = Field(None, max_length=20, examples=["+91-9876543210"])
    role: UserRole = Field(UserRole.VIEWER)

    model_config = {"from_attributes": True}


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["ravi@example.com"])
    password: str = Field(..., examples=["SecureP@ss1"])


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=120)
    phone: str | None = Field(None, max_length=20)
    role: UserRole | None = None

    model_config = {"from_attributes": True}


# ── Response Schemas ───────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str
