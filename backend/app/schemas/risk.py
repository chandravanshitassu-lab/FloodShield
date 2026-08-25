"""Pydantic v2 schemas for Risk Assessment API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.risk import RiskLevel


class RiskAssessmentResponse(BaseModel):
    """Standard risk response — matches the spec exactly."""
    risk_score: int = Field(..., ge=0, le=100, examples=[82])
    risk_level: RiskLevel = Field(..., examples=["HIGH"])
    safe_window_hours: float = Field(..., ge=0.0, examples=[5.0])

    model_config = {"from_attributes": True}


class RiskAssessmentDetailResponse(RiskAssessmentResponse):
    """Extended risk response with factor breakdown."""
    id: int
    business_id: int
    flood_probability: float | None
    water_level_cm: float | None
    rainfall_mm: float | None
    distance_to_river_km: float | None
    elevation_risk_factor: float | None
    historical_flood_count: int | None
    factor_breakdown: dict | None
    assessed_by: str
    notes: str | None
    assessed_at: datetime
    valid_until: datetime | None

    model_config = {"from_attributes": True}


class ManualRiskCreateRequest(BaseModel):
    """Payload for manually overriding / logging a risk assessment."""
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    safe_window_hours: float = Field(..., ge=0.0)
    flood_probability: float | None = Field(None, ge=0.0, le=1.0)
    water_level_cm: float | None = Field(None, ge=0.0)
    rainfall_mm: float | None = Field(None, ge=0.0)
    notes: str | None = Field(None, max_length=1000)

    model_config = {"from_attributes": True}


class RiskHistoryResponse(BaseModel):
    total: int
    items: list[RiskAssessmentDetailResponse]
