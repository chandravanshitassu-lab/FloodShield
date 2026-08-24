"""
Route Optimisation router — compute and manage evacuation routes.
Prefix: /api/routes
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.route import Route
from app.models.user import User
from app.schemas.route import (
    RouteComputeRequest,
    RouteUpdateRequest,
    RouteResponse,
    RouteListResponse,
)
from app.services import route_service
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/routes", tags=["Route Optimisation"])


def _get_or_404(db: Session, route_id: int) -> Route:
    r = db.get(Route, route_id)
    if not r:
        raise NotFoundError("Route", route_id)
    return r


@router.get("", response_model=RouteListResponse, summary="List computed routes")
def list_routes(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    business_id: int | None = Query(None),
    vehicle_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Return all routes; filter by business or vehicle if provided."""
    q = db.query(Route)
    if business_id:
        q = q.filter(Route.business_id == business_id)
    if vehicle_id:
        q = q.filter(Route.vehicle_id == vehicle_id)
    total = q.count()
    items = q.order_by(Route.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return RouteListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "/compute",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Compute a flood-safe route",
)
def compute_route(
    payload: RouteComputeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Request a flood-aware route computation between two coordinates.

    The service calls the external Route Engine to get an optimised,
    flood-zone-avoiding path. Falls back to a straight-line estimate
    when the engine is unavailable.
    """
    return route_service.compute_route(db, payload)


@router.get("/{route_id}", response_model=RouteResponse, summary="Get route by ID")
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_or_404(db, route_id)


@router.patch(
    "/{route_id}",
    response_model=RouteResponse,
    summary="Update route status or notes",
)
def update_route(
    route_id: int,
    payload: RouteUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Update the status (active/completed/cancelled) or add notes to a route."""
    r = _get_or_404(db, route_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    db.commit()
    db.refresh(r)
    return r


@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a route",
)
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    r = _get_or_404(db, route_id)
    db.delete(r)
    db.commit()
