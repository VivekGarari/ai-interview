from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from app.models.users import User
from app.schemas.auth import (
    SignupRequest, LoginRequest, RefreshRequest,
    UpdateProfileRequest, ChangePasswordRequest, TokenResponse, UserResponse, MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── POST /auth/signup ─────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and return tokens immediately (no email verify step for MVP)."""

    # Check email not already taken
    existing = db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        target_role=body.target_role,
        experience_level=body.experience_level,
    )
    db.add(user)
    db.flush()  # get the generated id without committing yet

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ── POST /auth/login ──────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return fresh tokens."""

    result = db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always run verify_password even on missing user to prevent timing attacks
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


# ── POST /auth/refresh ────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""

    user_id = decode_token(body.refresh_token, expected_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


# ── GET /auth/me ──────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


# ── PATCH /auth/me ────────────────────────────────────

@router.patch("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile fields (name, target role, experience level)."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.target_role is not None:
        current_user.target_role = body.target_role
    if body.experience_level is not None:
        current_user.experience_level = body.experience_level

    return UserResponse.model_validate(current_user)


# ── POST /auth/logout ─────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    """
    Stateless logout — client simply discards tokens.
    For full token revocation, store a blocklist in Redis (add later).
    """
    return MessageResponse(message="Logged out successfully.")


# ── POST /auth/change-password ────────────────────────

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password after verifying current password."""
    import bcrypt
    if not bcrypt.checkpw(body.current_password.encode(), current_user.hashed_password.encode()):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
    db.add(current_user)
    db.commit()
    return MessageResponse(message="Password changed successfully.")