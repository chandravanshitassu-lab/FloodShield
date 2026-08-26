"""Pydantic v2 schemas for Business API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.business import BusinessType, BusinessStatus


class BusinessCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["Sharma Pharma Pvt. Ltd."])
    registration_number: str | None = Field(None, max_length=100)
    business_type: BusinessType = BusinessType.OTHER
    description: str | None = None
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    elevation_meters: float | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
    employee_count: int = Field(0, ge=0)
    estimated_asset_value: float = Field(0.0, ge=0.0)
    is_critical_infrastructure: bool = False

    model_config = {"from_attributes": True}


class BusinessUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = Field(None, pattern=r"^\d{6}$")
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    elevation_meters: float | None = None
    status: BusinessStatus | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    employee_count: int | None = Field(None, ge=0)
    estimated_asset_value: float | None = Field(None, ge=0.0)
    is_critical_infrastructure: bool | None = None

    model_config = {"from_attributes": True}


class BusinessResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    registration_number: str | None
    business_type: BusinessType
    description: str | None
    address: str
    city: str
    state: str
    pincode: str
    latitude: float | None
    longitude: float | None
    elevation_meters: float | None
    status: BusinessStatus
    contact_email: str | None
    contact_phone: str | None
    employee_count: int
    estimated_asset_value: float
    is_critical_infrastructure: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BusinessResponse]
