import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    """Target job role the user is practicing for."""
    SOFTWARE_ENGINEER ="software_engineer"
    DATA_SCIENTIST ="data_scientist"
    PRODUCT_MANAGER = "produc_manager"
    DESIGNER = "designer"
    DEVOPS = "devops"
    OTHER = "other"

class ExperienceLevel(str, enum.Enum):
    JUNIOR="junior"     # 0 - 2 years
    MID="mid"           # 2 - 5 years
    SENIOR="senior"     # 5 - 10 years
    STAFF="staff"       # 10+ years

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile
    target_role: Mapped[str] = mapped_column(

        SAEnum(UserRole), default=UserRole.SOFTWARE_ENGINEER
    )
    experience_level: Mapped[str] = mapped_column(
        SAEnum(ExperienceLevel), default=ExperienceLevel.JUNIOR
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


    # Relationships (defined here, loaded lazily)
    sessions: Mapped[list["InterviewSession"]]= relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    code_submissions: Mapped[list["CodeSubmission"]] = relationship(
    back_populates="user", cascade="all, delete-orphan"
)

    def __repr__(self):
        return f"<User {self.email}>"