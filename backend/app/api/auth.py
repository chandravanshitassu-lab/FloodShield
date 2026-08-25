"""
Authentication router — registration, login, token refresh, logout, profile.
All endpoints are prefixed with /api/auth by the main router aggregator.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserUpdateRequest,
)
from app.services import auth_service
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new FloodShield account.

    - **full_name**: Display name (2–120 chars)
    - **email**: Unique email address
    - **password**: Min 8 characters
    - **role**: One of admin | business_owner | warehouse_manager | fleet_manager | viewer
    """
    user = auth_service.register_user(db, payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain JWT access and refresh tokens",
)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password and receive JWT tokens.
    Use the **access_token** as `Authorization: Bearer <token>` on all protected routes.
    """
    return auth_service.login_user(db, payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    return auth_service.refresh_access_token(db, payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token and log out",
)
def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke the stored refresh token, effectively ending all sessions."""
    auth_service.logout_user(db, current_user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user profile",
)
def me(current_user: User = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
)
def update_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Partially update the current user's display name, phone, or role."""
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change the password for the current user. Invalidates all active sessions."""
    auth_service.change_password(
        db, current_user, payload.current_password, payload.new_password
    )
