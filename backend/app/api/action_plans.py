"""
Action Plans router — contingency and mitigation plans.
Prefix: /api/businesses/{business_id}/action-plans
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.action_plan import ActionPlan
from app.models.user import User, UserRole
from app.schemas.action_plan import (
    ActionPlanCreateRequest,
    ActionPlanUpdateRequest,
    ActionPlanResponse,
    ActionPlanListResponse,
)
from app.services import action_plan_service
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError

router = APIRouter(
    prefix="/businesses/{business_id}/action-plans",
    tags=["Action Plans"],
)


def _get_or_404(db: Session, plan_id: int, business_id: int) -> ActionPlan:
    plan = (
        db.query(ActionPlan)
        .filter(ActionPlan.id == plan_id, ActionPlan.business_id == business_id)
        .first()
    )
    if not plan:
        raise NotFoundError("ActionPlan", plan_id)
    return plan


@router.get("", response_model=ActionPlanListResponse, summary="List action plans")
def list_action_plans(
    business_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Return all action plans for a business, ordered by priority."""
    q = (
        db.query(ActionPlan)
        .filter(ActionPlan.business_id == business_id)
        .order_by(ActionPlan.priority, ActionPlan.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return ActionPlanListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=ActionPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an action plan",
)
def create_action_plan(
    business_id: int,
    payload: ActionPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new contingency plan for a business."""
    return action_plan_service.create_action_plan(db, business_id, payload, current_user.id)


@router.get(
    "/{plan_id}", response_model=ActionPlanResponse, summary="Get action plan by ID"
)
def get_action_plan(
    business_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_or_404(db, plan_id, business_id)


@router.patch(
    "/{plan_id}", response_model=ActionPlanResponse, summary="Update action plan"
)
def update_action_plan(
    business_id: int,
    plan_id: int,
    payload: ActionPlanUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    plan = _get_or_404(db, plan_id, business_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "steps" and value is not None:
            value = [s.model_dump() if hasattr(s, "model_dump") else s for s in value]
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.post(
    "/{plan_id}/activate",
    response_model=ActionPlanResponse,
    summary="Activate an action plan",
)
def activate_plan(
    business_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Set the plan to IN_PROGRESS and record the activation timestamp."""
    _get_or_404(db, plan_id, business_id)  # ownership check
    return action_plan_service.activate_action_plan(db, plan_id)


@router.post(
    "/{plan_id}/complete",
    response_model=ActionPlanResponse,
    summary="Mark an action plan as completed",
)
def complete_plan(
    business_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Mark the action plan as COMPLETED."""
    _get_or_404(db, plan_id, business_id)
    return action_plan_service.complete_action_plan(db, plan_id)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an action plan",
)
def delete_action_plan(
    business_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    plan = _get_or_404(db, plan_id, business_id)
    db.delete(plan)
    db.commit()
