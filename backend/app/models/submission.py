import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CodingProblem(Base):
    """A coding challenge (pre-seeded or AI-generated)."""
    __tablename__ = "coding_problems"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # easy/medium/hard
    topic: Mapped[str] = mapped_column(String(50), nullable=False)       # arrays, dp, trees, etc.
    examples: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hints: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # hidden from user
    test_cases: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    submissions: Mapped[list["CodeSubmission"]] = relationship(back_populates="problem")


class CodeSubmission(Base):
    """A user's code submission for a problem."""
    __tablename__ = "code_submissions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[str] = mapped_column(
        String, ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False
    )

    language: Mapped[str] = mapped_column(String(30), nullable=False)  # python, javascript, java
    code: Mapped[str] = mapped_column(Text, nullable=False)

    # Execution results
    passed_tests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    runtime_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI code review
    ai_review: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="code_submissions")
    problem: Mapped["CodingProblem"] = relationship(back_populates="submissions")