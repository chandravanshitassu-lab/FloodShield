"""Pydantic v2 schemas for Vehicle API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.vehicle import VehicleType, VehicleStatus


class VehicleCreateRequest(BaseModel):
    registration_number: str = Field(..., min_length=3, max_length=50, examples=["MH12AB1234"])
    vehicle_type: VehicleType
    make: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    year: int | None = Field(None, ge=1980, le=2030)
    payload_capacity_tons: float = Field(0.0, ge=0.0)
    passenger_capacity: int = Field(0, ge=0)
    volume_capacity_cbm: float | None = None
    driver_name: str | None = Field(None, max_length=120)
    driver_phone: str | None = Field(None, max_length=20)
    is_amphibious: bool = False
    fuel_level_pct: float | None = Field(None, ge=0.0, le=100.0)

    model_config = {"from_attributes": True}


class VehicleUpdateRequest(BaseModel):
    status: VehicleStatus | None = None
    current_latitude: float | None = Field(None, ge=-90.0, le=90.0)
    current_longitude: float | None = Field(None, ge=-180.0, le=180.0)
    driver_name: str | None = None
    driver_phone: str | None = None
    fuel_level_pct: float | None = Field(None, ge=0.0, le=100.0)
    payload_capacity_tons: float | None = Field(None, ge=0.0)

    model_config = {"from_attributes": True}


class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    vehicle_type: VehicleType
    make: str | None
    model: str | None
    year: int | None
    payload_capacity_tons: float
    passenger_capacity: int
    volume_capacity_cbm: float | None
    status: VehicleStatus
    current_latitude: float | None
    current_longitude: float | None
    last_location_update: datetime | None
    driver_name: str | None
    driver_phone: str | None
    is_amphibious: bool
    fuel_level_pct: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[VehicleResponse]
