from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.audit_service import log_event


def register_user(db: Session, payload: RegisterRequest) -> User:
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_event(
        db,
        action="user_registered",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        metadata={"email": user.email},
    )
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(subject=str(user.id), role=user.role.value)

    log_event(
        db,
        action="user_logged_in",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        metadata={"email": user.email},
    )

    return TokenResponse(access_token=token, user=user)
