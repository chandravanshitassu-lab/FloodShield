"""Pydantic v2 schemas for Warehouse API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.warehouse import WarehouseStatus


class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    operator_name: str | None = Field(None, max_length=200)
    description: str | None = None
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    elevation_meters: float = Field(0.0, ge=0.0)
    total_capacity_sqm: float = Field(0.0, ge=0.0)
    available_capacity_sqm: float = Field(0.0, ge=0.0)
    max_weight_tons: float | None = None
    is_flood_safe: bool = True
    has_power_backup: bool = False
    has_cold_storage: bool = False
    contact_phone: str | None = None
    contact_email: EmailStr | None = None

    model_config = {"from_attributes": True}


class WarehouseUpdateRequest(BaseModel):
    name: str | None = None
    operator_name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    available_capacity_sqm: float | None = Field(None, ge=0.0)
    status: WarehouseStatus | None = None
    is_flood_safe: bool | None = None
    contact_phone: str | None = None
    contact_email: str | None = None

    model_config = {"from_attributes": True}


class WarehouseResponse(BaseModel):
    id: int
    name: str
    operator_name: str | None
    description: str | None
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    elevation_meters: float
    total_capacity_sqm: float
    available_capacity_sqm: float
    max_weight_tons: float | None
    status: WarehouseStatus
    is_flood_safe: bool
    has_power_backup: bool
    has_cold_storage: bool
    contact_phone: str | None
    contact_email: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WarehouseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[WarehouseResponse]
