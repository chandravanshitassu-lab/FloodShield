"""
Warehouses router — CRUD for safe storage and evacuation facilities.
Prefix: /api/warehouses
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.warehouse import Warehouse
from app.models.user import User, UserRole
from app.schemas.warehouse import (
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
    WarehouseResponse,
    WarehouseListResponse,
)
from app.utils.dependencies import get_current_active_user, require_roles
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


def _get_or_404(db: Session, wh_id: int) -> Warehouse:
    wh = db.get(Warehouse, wh_id)
    if not wh:
        raise NotFoundError("Warehouse", wh_id)
    return wh


@router.get("", response_model=WarehouseListResponse, summary="List warehouses")
def list_warehouses(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    city: str | None = Query(None),
    flood_safe_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """List available warehouses; optionally filter by city or flood-safe flag."""
    q = db.query(Warehouse)
    if city:
        q = q.filter(Warehouse.city.ilike(f"%{city}%"))
    if flood_safe_only:
        q = q.filter(Warehouse.is_flood_safe.is_(True))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return WarehouseListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a warehouse",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))],
)
def create_warehouse(
    payload: WarehouseCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Create a new warehouse record. Admin or Warehouse Manager only."""
    wh = Warehouse(**payload.model_dump())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


@router.get("/{warehouse_id}", response_model=WarehouseResponse, summary="Get warehouse by ID")
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_or_404(db, warehouse_id)


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Update warehouse",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))],
)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    wh = _get_or_404(db, warehouse_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(wh, field, value)
    db.commit()
    db.refresh(wh)
    return wh


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete warehouse",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    wh = _get_or_404(db, warehouse_id)
    db.delete(wh)
    db.commit()
