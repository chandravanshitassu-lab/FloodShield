"""Pydantic v2 schemas for Route API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.route import RouteStatus


class RouteComputeRequest(BaseModel):
    """Request a new flood-safe route computation."""
    business_id: int | None = None
    vehicle_id: int | None = None
    destination_warehouse_id: int | None = None
    origin_address: str = Field(..., min_length=5)
    origin_latitude: float = Field(..., ge=-90.0, le=90.0)
    origin_longitude: float = Field(..., ge=-180.0, le=180.0)
    destination_address: str = Field(..., min_length=5)
    destination_latitude: float = Field(..., ge=-90.0, le=90.0)
    destination_longitude: float = Field(..., ge=-180.0, le=180.0)
    notes: str | None = None

    model_config = {"from_attributes": True}


class RouteUpdateRequest(BaseModel):
    status: RouteStatus | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class RouteResponse(BaseModel):
    id: int
    business_id: int | None
    vehicle_id: int | None
    destination_warehouse_id: int | None
    origin_address: str
    origin_latitude: float
    origin_longitude: float
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    distance_km: float | None
    estimated_duration_min: int | None
    waypoints: list | None
    flood_risk_zones: list | None
    is_flood_safe: bool
    safety_score: float | None
    status: RouteStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RouteListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RouteResponse]
