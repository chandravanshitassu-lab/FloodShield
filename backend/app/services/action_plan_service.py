"""
Action Plan service — creates, activates, and completes contingency plans.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.action_plan import ActionPlan, PlanStatus, PlanTrigger
from app.models.business import Business
from app.schemas.action_plan import ActionPlanCreateRequest
from app.schemas.route import RouteComputeRequest
from app.services.storage_engine import find_safe_warehouse
from app.services.transport_engine import find_best_transport
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
    Auto-generate a smart evacuation plan using Member 4 logistics engines.

    Triggered when flood risk score >= 70. Coordinates the full logistics
    pipeline:
      1. Compute total inventory weight (tons) from the business's inventory.
      2. Match the nearest flood-safe warehouse with adequate capacity.
      3. Match the closest available vehicle meeting the payload requirement.
      4. Compute and persist a safe evacuation route (if warehouse found).
      5. Build tailored, dynamic action steps and persist the ActionPlan.
    """
    business = db.get(Business, business_id)
    if not business:
        raise NotFoundError("Business", business_id)

    # 1. Compute total inventory weight (fallback to 3.0 tons if unitless or 0)
    total_weight = sum(
        inv.quantity
        for inv in business.inventories
        if inv.unit and inv.unit.lower() in ["ton", "tons", "t"]
    )
    if total_weight <= 0:
        total_weight = 3.0

    # 2. Match Safe Warehouse and Available Fleet
    safe_wh = find_safe_warehouse(db, business, required_weight_tons=total_weight)
    matched_vehicle = find_best_transport(db, business, required_weight_tons=total_weight)

    # 3. Compute and persist Safe Evacuation Route if warehouse found
    if safe_wh and business.latitude and business.longitude:
        from app.services.route_service import compute_route  # local import avoids circular dep

        route_req = RouteComputeRequest(
            business_id=business.id,
            vehicle_id=matched_vehicle.id if matched_vehicle else None,
            destination_warehouse_id=safe_wh.id,
            origin_address=business.address,
            origin_latitude=business.latitude,
            origin_longitude=business.longitude,
            destination_address=safe_wh.address,
            destination_latitude=safe_wh.latitude,
            destination_longitude=safe_wh.longitude,
            notes="Automated emergency route generated from high flood risk trigger.",
        )
        compute_route(db, route_req)

    # 4. Construct tailored dynamic action steps
    steps = [
        {
            "order": 1,
            "action": "Alert all staff and trigger priority evacuation protocol",
            "responsible": "Business Manager",
            "done": False,
        },
        {
            "order": 2,
            "action": (
                f"Dispatch vehicle {matched_vehicle.registration_number} "
                f"(Type: {matched_vehicle.vehicle_type.value}, "
                f"Payload: {matched_vehicle.payload_capacity_tons}T)"
                if matched_vehicle
                else "Request urgent external transport fleet allocation"
            ),
            "responsible": "Fleet Coordinator",
            "done": False,
        },
        {
            "order": 3,
            "action": (
                f"Transport ~{total_weight}T inventory via verified safe route "
                f"to {safe_wh.name} ({safe_wh.address})"
                if safe_wh
                else "Elevate and seal inventory on-site (No external safe warehouse found)"
            ),
            "responsible": "Logistics Lead",
            "done": False,
        },
        {
            "order": 4,
            "action": "Final facility lockdown and submit evacuation completion report",
            "responsible": "Operations Lead",
            "done": False,
        },
    ]

    plan = ActionPlan(
        business_id=business_id,
        title=f"Auto-Generated Flood Evacuation Plan (Risk Score: {risk_score})",
        description=(
            "Automated logistics allocation. Safe Warehouse: "
            f"{safe_wh.name if safe_wh else 'None Available'}, "
            f"Assigned Vehicle: "
            f"{matched_vehicle.registration_number if matched_vehicle else 'Pending Dispatch'}."
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

