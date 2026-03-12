import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class InterviewType(str, enum.Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SYSTEM_DESIGN = "system_design"
    HR = "hr"
    CODING = "coding"
    MIXED = "mixed"


class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Session config
    interview_type: Mapped[str] = mapped_column(SAEnum(InterviewType), nullable=False)
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy/medium/hard
    status: Mapped[str] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.IN_PROGRESS)

    # Results (filled on completion)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)    # list of strings
    improvements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # list of strings

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Video recording (optional)
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    questions: Mapped[list["SessionQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="SessionQuestion.order_index"
    )

    def __repr__(self):
        return f"<InterviewSession {self.id} [{self.interview_type}]>"


class SessionQuestion(Base):
    """Each Q&A exchange within a session."""
    __tablename__ = "session_questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Question #1, #2, etc.
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI evaluation of this specific answer
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)        # 0–10
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_asked: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # AI follow-up question

    # Metadata
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    asked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    session: Mapped["InterviewSession"] = relationship(back_populates="questions")