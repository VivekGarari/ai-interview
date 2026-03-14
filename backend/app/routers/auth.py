import random
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from app.models.users import User
from app.schemas.auth import (
    SignupRequest, LoginRequest, RefreshRequest,
    UpdateProfileRequest, ChangePasswordRequest,
    VerifyEmailRequest, ResendOTPRequest,
    TokenResponse, UserResponse, MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── POST /auth/signup ─────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    from app.services.email_service import email_service

    existing = db.execute(select(User).where(User.email == body.email)).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    otp = str(random.randint(100000, 999999))
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        target_role=body.target_role,
        experience_level=body.experience_level,
        is_verified=False,
        otp_code=otp,
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    email_service.send_otp(user.email, user.full_name, otp)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


# ── POST /auth/login ──────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email)).scalars().first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


# ── POST /auth/refresh ────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(body: RefreshRequest, db: Session = Depends(get_db)):
    user_id = decode_token(body.refresh_token, expected_type="refresh")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    user = db.execute(select(User).where(User.id == user_id)).scalars().first()
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
    return UserResponse.model_validate(current_user)


# ── PATCH /auth/me ────────────────────────────────────

@router.patch("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.target_role is not None:
        current_user.target_role = body.target_role
    if body.experience_level is not None:
        current_user.experience_level = body.experience_level
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


# ── POST /auth/change-password ────────────────────────

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not bcrypt.checkpw(body.current_password.encode(), current_user.hashed_password.encode()):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.hashed_password = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return MessageResponse(message="Password changed successfully.")


# ── POST /auth/logout ─────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    return MessageResponse(message="Logged out successfully.")


# ── POST /auth/verify-email ───────────────────────────

@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified:
        return MessageResponse(message="Email already verified.")
    if not user.otp_code or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")
    if datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if user.otp_code != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    return MessageResponse(message="Email verified successfully!")


# ── POST /auth/resend-otp ─────────────────────────────

@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(body: ResendOTPRequest, db: Session = Depends(get_db)):
    from app.services.email_service import email_service

    user = db.execute(select(User).where(User.email == body.email)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified:
        return MessageResponse(message="Email already verified.")

    otp = str(random.randint(100000, 999999))
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    email_service.send_otp(user.email, user.full_name, otp)
    return MessageResponse(message="OTP sent to your email.")


# ── POST /auth/reset-password-temp (remove after use) ─

@router.post("/reset-password-temp")
def reset_password_temp(
    email: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    user = db.execute(select(User).where(User.email == email)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.hashed_password = hash_password(new_password)
    user.is_verified = True
    db.commit()
    return {"message": "Password reset successfully!"}