"""
Admin router — system-wide metrics, user management, and monitoring.
All endpoints require the ADMIN role.
Prefix: /api/admin
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.business import Business, BusinessStatus
from app.models.inventory import Inventory
from app.models.risk import RiskAssessment, RiskLevel
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.warehouse import Warehouse
from app.models.action_plan import ActionPlan
from app.schemas.user import UserResponse, UserUpdateRequest
from app.utils.dependencies import get_current_active_user, require_roles
from app.utils.exceptions import NotFoundError
from pydantic import BaseModel

router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)


# ── Dashboard / Metrics ────────────────────────────────────────────────────

class SystemMetrics(BaseModel):
    total_users: int
    total_businesses: int
    businesses_evacuating: int
    businesses_evacuated: int
    total_warehouses: int
    total_vehicles: int
    vehicles_in_transit: int
    high_risk_businesses: int
    critical_risk_businesses: int
    total_action_plans: int
    active_action_plans: int
    total_inventory_value_inr: float


@router.get("/metrics", response_model=SystemMetrics, summary="System-wide dashboard metrics")
def get_system_metrics(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Return aggregated system-wide statistics for the admin dashboard.
    Includes entity counts, risk distribution, and fleet status.
    """
    # Business stats
    total_businesses = db.query(func.count(Business.id)).scalar() or 0
    biz_evacuating = (
        db.query(func.count(Business.id))
        .filter(Business.status == BusinessStatus.EVACUATING)
        .scalar()
        or 0
    )
    biz_evacuated = (
        db.query(func.count(Business.id))
        .filter(Business.status == BusinessStatus.EVACUATED)
        .scalar()
        or 0
    )

    # Latest risk per business (subquery approach)
    high_risk = (
        db.query(func.count(RiskAssessment.id))
        .filter(RiskAssessment.risk_level == RiskLevel.HIGH)
        .scalar()
        or 0
    )
    critical_risk = (
        db.query(func.count(RiskAssessment.id))
        .filter(RiskAssessment.risk_level == RiskLevel.CRITICAL)
        .scalar()
        or 0
    )

    # Vehicle stats
    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    in_transit = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.status == VehicleStatus.IN_TRANSIT)
        .scalar()
        or 0
    )

    # Inventory value
    total_inv_value = db.query(func.sum(Inventory.total_value)).scalar() or 0.0

    # Action plans
    from app.models.action_plan import PlanStatus
    total_plans = db.query(func.count(ActionPlan.id)).scalar() or 0
    active_plans = (
        db.query(func.count(ActionPlan.id))
        .filter(ActionPlan.status == PlanStatus.IN_PROGRESS)
        .scalar()
        or 0
    )

    return SystemMetrics(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_businesses=total_businesses,
        businesses_evacuating=biz_evacuating,
        businesses_evacuated=biz_evacuated,
        total_warehouses=db.query(func.count(Warehouse.id)).scalar() or 0,
        total_vehicles=total_vehicles,
        vehicles_in_transit=in_transit,
        high_risk_businesses=high_risk,
        critical_risk_businesses=critical_risk,
        total_action_plans=total_plans,
        active_action_plans=active_plans,
        total_inventory_value_inr=float(total_inv_value),
    )


# ── User Management ────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse], summary="List all users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: UserRole | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Paginated list of all registered users with optional role filter."""
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update user")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Admin: update any user's details (name, phone, role)."""
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", summary="Deactivate a user account")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_user),
):
    """Deactivate a user (soft delete). Cannot deactivate yourself."""
    if user_id == current_admin.id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account.",
        )
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    user.is_active = False
    db.commit()
    return {"message": f"User {user_id} deactivated successfully."}


@router.post("/users/{user_id}/activate", summary="Re-activate a user account")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    user.is_active = True
    db.commit()
    return {"message": f"User {user_id} activated successfully."}
