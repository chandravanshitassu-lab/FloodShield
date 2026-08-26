"""
Businesses router — full CRUD for registered commercial entities.
Prefix: /api/businesses
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.business import Business
from app.models.user import User, UserRole
from app.schemas.business import (
    BusinessCreateRequest,
    BusinessUpdateRequest,
    BusinessResponse,
    BusinessListResponse,
)
from app.utils.dependencies import get_current_active_user, require_roles
from app.utils.exceptions import NotFoundError, ForbiddenError

router = APIRouter(prefix="/businesses", tags=["Businesses"])


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, business_id: int) -> Business:
    biz = db.get(Business, business_id)
    if not biz:
        raise NotFoundError("Business", business_id)
    return biz


def _assert_owner_or_admin(user: User, business: Business) -> None:
    if user.role != UserRole.ADMIN and business.owner_id != user.id:
        raise ForbiddenError("You do not have permission to modify this business.")


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=BusinessListResponse, summary="List all businesses")
def list_businesses(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    city: str | None = Query(None),
    state: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Paginated list of businesses with optional city/state filters."""
    q = db.query(Business)
    if city:
        q = q.filter(Business.city.ilike(f"%{city}%"))
    if state:
        q = q.filter(Business.state.ilike(f"%{state}%"))

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return BusinessListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new business",
)
def create_business(
    payload: BusinessCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Register a new commercial entity under the authenticated owner."""
    biz = Business(**payload.model_dump(), owner_id=current_user.id)
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


@router.get("/{business_id}", response_model=BusinessResponse, summary="Get business by ID")
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return _get_or_404(db, business_id)


@router.patch(
    "/{business_id}", response_model=BusinessResponse, summary="Partially update a business"
)
def update_business(
    business_id: int,
    payload: BusinessUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update business fields. Only the owner or an admin may call this."""
    biz = _get_or_404(db, business_id)
    _assert_owner_or_admin(current_user, biz)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(biz, field, value)
    db.commit()
    db.refresh(biz)
    return biz


@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a business",
)
def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Permanently delete a business record. Owner or admin only."""
    biz = _get_or_404(db, business_id)
    _assert_owner_or_admin(current_user, biz)
    db.delete(biz)
    db.commit()
