"""
Authentication business-logic service.
Handles registration, login, token refresh, and password changes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegisterRequest, UserLoginRequest
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.utils.exceptions import ConflictError, UnauthorizedError, NotFoundError
from app.database.config import settings


def register_user(db: Session, payload: UserRegisterRequest) -> User:
    """
    Register a new user.

    Raises:
        ConflictError: if the email is already taken.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise ConflictError(f"Email {payload.email!r} is already registered.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, payload: UserLoginRequest) -> dict:
    """
    Authenticate a user and return access + refresh tokens.

    Raises:
        UnauthorizedError: if credentials are wrong or account is inactive.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated. Contact an administrator.")

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    # Persist refresh token + last_login
    user.refresh_token = refresh_token
    user.last_login = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    Issue a new access token from a valid refresh token.

    Raises:
        UnauthorizedError: on invalid / mismatched token.
    """
    from jose import JWTError

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired refresh token.")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Token type mismatch.")

    user = db.get(User, int(payload["sub"]))
    if not user or user.refresh_token != refresh_token:
        raise UnauthorizedError("Refresh token has been revoked.")

    new_access = create_access_token(user.id, user.role.value)
    return {
        "access_token": new_access,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def logout_user(db: Session, user: User) -> None:
    """Revoke the stored refresh token."""
    user.refresh_token = None
    db.commit()


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    """
    Change user password after verifying the current one.

    Raises:
        UnauthorizedError: if current password is wrong.
    """
    if not verify_password(current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect.")
    user.hashed_password = hash_password(new_password)
    user.refresh_token = None   # invalidate all sessions
    db.commit()
