"""
Action Plan service — creates, activates, and completes contingency plans.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.action_plan import ActionPlan, PlanStatus, PlanTrigger
from app.models.business import Business
from app.schemas.action_plan import ActionPlanCreateRequest
from app.utils.exceptions import NotFoundError


def create_action_plan(
    db: Session, business_id: int, payload: ActionPlanCreateRequest, user_id: int
) -> ActionPlan:
    """Create a new contingency / mitigation plan for a business."""
    business = db.get(Business, business_id)
    if not business:
        raise NotFoundError("Business", business_id)

    steps_data = [s.model_dump() for s in payload.steps] if payload.steps else []

    plan = ActionPlan(
        business_id=business_id,
        created_by_user_id=user_id,
        title=payload.title,
        description=payload.description,
        trigger=payload.trigger,
        steps=steps_data,
        priority=payload.priority,
        target_completion_hours=payload.target_completion_hours,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def activate_action_plan(db: Session, plan_id: int) -> ActionPlan:
    """Set a plan to IN_PROGRESS and record activation time."""
    plan = db.get(ActionPlan, plan_id)
    if not plan:
        raise NotFoundError("ActionPlan", plan_id)

    plan.status = PlanStatus.IN_PROGRESS
    plan.activated_at = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def complete_action_plan(db: Session, plan_id: int) -> ActionPlan:
    """Mark a plan as COMPLETED."""
    plan = db.get(ActionPlan, plan_id)
    if not plan:
        raise NotFoundError("ActionPlan", plan_id)

    plan.status = PlanStatus.COMPLETED
    plan.completed_at = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def auto_generate_plan(db: Session, business_id: int, risk_score: int) -> ActionPlan:
    """
    Auto-generate a templated action plan when risk crosses a threshold.
    Called by the Risk endpoint when risk_score >= 70.
    """
    business = db.get(Business, business_id)
    if not business:
        raise NotFoundError("Business", business_id)

    steps = [
        {"order": 1, "action": "Alert all staff and initiate emergency protocol", "done": False},
        {"order": 2, "action": "Identify and prioritise high-value/perishable inventory", "done": False},
        {"order": 3, "action": "Contact nearest safe warehouse for capacity confirmation", "done": False},
        {"order": 4, "action": "Deploy available vehicles for inventory evacuation", "done": False},
        {"order": 5, "action": "Secure critical documents and digital backups", "done": False},
        {"order": 6, "action": "Complete evacuation and report status to admin", "done": False},
    ]

    plan = ActionPlan(
        business_id=business_id,
        title=f"Auto-Generated Flood Response Plan (Risk Score: {risk_score})",
        description=(
            "Automatically triggered because the risk score exceeded the HIGH threshold. "
            "Review and customise steps before activation."
        ),
        trigger=PlanTrigger.RISK_THRESHOLD,
        status=PlanStatus.ACTIVE,
        steps=steps,
        priority=1,
        target_completion_hours=6,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
