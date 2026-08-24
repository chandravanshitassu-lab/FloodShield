"""
Vehicles router — evacuation fleet management.
Prefix: /api/vehicles
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.vehicle import Vehicle
from app.models.user import User, UserRole
from app.schemas.vehicle import (
    VehicleCreateRequest,
    VehicleUpdateRequest,
    VehicleResponse,
    VehicleListResponse,
)
from app.utils.dependencies import get_current_active_user, require_roles
from app.utils.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


def _get_or_404(db: Session, vehicle_id: int) -> Vehicle:
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise NotFoundError("Vehicle", vehicle_id)
    return v


@router.get("", response_model=VehicleListResponse, summary="List fleet")
def list_vehicles(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = Query(None, alias="status"),
    vehicle_type: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """List all fleet vehicles with optional status/type filters."""
    q = db.query(Vehicle)
    if status_filter:
        q = q.filter(Vehicle.status == status_filter)
    if vehicle_type:
        q = q.filter(Vehicle.vehicle_type == vehicle_type)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return VehicleListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a vehicle to the fleet",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.FLEET_MANAGER))],
)
def create_vehicle(
    payload: VehicleCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Register a new vehicle. Admin or Fleet Manager only."""
    existing = db.query(Vehicle).filter(
        Vehicle.registration_number == payload.registration_number
    ).first()
    if existing:
        raise ConflictError(
            f"Vehicle with registration {payload.registration_number!r} already exists."
        )
    v = Vehicle(**payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/{vehicle_id}", response_model=VehicleResponse, summary="Get vehicle by ID")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_or_404(db, vehicle_id)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle (status, location, driver)",
)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Update vehicle fields.
    Drivers use this endpoint to push GPS location and status updates.
    """
    v = _get_or_404(db, vehicle_id)
    update_data = payload.model_dump(exclude_none=True)

    # If location is updated, stamp the timestamp
    if "current_latitude" in update_data or "current_longitude" in update_data:
        update_data["last_location_update"] = datetime.now(tz=timezone.utc)

    for field, value in update_data.items():
        setattr(v, field, value)
    db.commit()
    db.refresh(v)
    return v


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a vehicle",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    v = _get_or_404(db, vehicle_id)
    db.delete(v)
    db.commit()
