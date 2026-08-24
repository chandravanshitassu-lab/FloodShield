"""Pydantic v2 schemas for ActionPlan API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.action_plan import PlanStatus, PlanTrigger


class ActionStep(BaseModel):
    order: int
    action: str
    responsible: str | None = None
    done: bool = False
    notes: str | None = None


class ActionPlanCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str | None = None
    trigger: PlanTrigger = PlanTrigger.MANUAL
    steps: list[ActionStep] | None = None
    priority: int = Field(3, ge=1, le=5)
    target_completion_hours: int | None = Field(None, ge=1)

    model_config = {"from_attributes": True}


class ActionPlanUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=300)
    description: str | None = None
    status: PlanStatus | None = None
    steps: list[ActionStep] | None = None
    priority: int | None = Field(None, ge=1, le=5)
    target_completion_hours: int | None = None

    model_config = {"from_attributes": True}


class ActionPlanResponse(BaseModel):
    id: int
    business_id: int
    created_by_user_id: int | None
    title: str
    description: str | None
    trigger: PlanTrigger
    status: PlanStatus
    steps: list | None
    priority: int
    target_completion_hours: int | None
    activated_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionPlanListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ActionPlanResponse]
