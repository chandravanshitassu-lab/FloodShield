"""
Inventory router — CRUD for stock items scoped to a specific business.
Prefix: /api/businesses/{business_id}/inventory
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.inventory import Inventory
from app.models.user import User, UserRole
from app.models.business import Business
from app.schemas.inventory import (
    InventoryCreateRequest,
    InventoryUpdateRequest,
    InventoryResponse,
    InventoryListResponse,
    StockAdjustRequest,
)
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError, ForbiddenError

router = APIRouter(
    prefix="/businesses/{business_id}/inventory",
    tags=["Inventory"],
)


def _get_business_or_404(db: Session, business_id: int) -> Business:
    biz = db.get(Business, business_id)
    if not biz:
        raise NotFoundError("Business", business_id)
    return biz


def _get_item_or_404(db: Session, item_id: int, business_id: int) -> Inventory:
    item = (
        db.query(Inventory)
        .filter(Inventory.id == item_id, Inventory.business_id == business_id)
        .first()
    )
    if not item:
        raise NotFoundError("Inventory item", item_id)
    return item


def _assert_access(user: User, business: Business) -> None:
    if user.role != UserRole.ADMIN and business.owner_id != user.id:
        raise ForbiddenError("Access denied for this business inventory.")


@router.get("", response_model=InventoryListResponse, summary="List inventory")
def list_inventory(
    business_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all inventory items for a given business (paginated)."""
    biz = _get_business_or_404(db, business_id)
    q = db.query(Inventory).filter(Inventory.business_id == business_id)
    if category:
        q = q.filter(Inventory.category == category)
    total = q.count()
    items = q.order_by(Inventory.evacuation_priority).offset((page - 1) * page_size).limit(page_size).all()
    return InventoryListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add inventory item",
)
def create_inventory(
    business_id: int,
    payload: InventoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new inventory item to a business."""
    biz = _get_business_or_404(db, business_id)
    _assert_access(current_user, biz)
    total_value = payload.quantity * payload.unit_value
    item = Inventory(
        **payload.model_dump(),
        business_id=business_id,
        total_value=total_value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=InventoryResponse, summary="Get inventory item")
def get_inventory_item(
    business_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_item_or_404(db, item_id, business_id)


@router.patch(
    "/{item_id}", response_model=InventoryResponse, summary="Update inventory item"
)
def update_inventory_item(
    business_id: int,
    item_id: int,
    payload: InventoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    biz = _get_business_or_404(db, business_id)
    _assert_access(current_user, biz)
    item = _get_item_or_404(db, item_id, business_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    item.total_value = item.quantity * item.unit_value
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/{item_id}/adjust",
    response_model=InventoryResponse,
    summary="Adjust stock quantity",
)
def adjust_stock(
    business_id: int,
    item_id: int,
    payload: StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Increment or decrement item quantity without a full update."""
    biz = _get_business_or_404(db, business_id)
    _assert_access(current_user, biz)
    item = _get_item_or_404(db, item_id, business_id)
    item.quantity = max(0.0, item.quantity + payload.delta)
    item.total_value = item.quantity * item.unit_value
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory item",
)
def delete_inventory_item(
    business_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    biz = _get_business_or_404(db, business_id)
    _assert_access(current_user, biz)
    item = _get_item_or_404(db, item_id, business_id)
    db.delete(item)
    db.commit()
