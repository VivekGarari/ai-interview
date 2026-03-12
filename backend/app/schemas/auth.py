from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.users import UserRole, ExperienceLevel


# ── Request schemas (what the client sends) ───────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=2, max_length=100)
    target_role: str = "software_engineer"
    experience_level: str = "junior"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    target_role: Optional[str] = None
    experience_level: Optional[str] = None


# ── Response schemas (what we send back) ─────────────

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    target_role: str
    experience_level: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)