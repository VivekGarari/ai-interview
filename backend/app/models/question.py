import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuestionDifficulty(str, enum.Enum):
	EASY = "easy"
	MEDIUM = "medium"
	HARD = "hard"


class QuestionType(str, enum.Enum):
	MCQ = "mcq"
	THEORY = "theory"
	CODING = "coding"


class Domain(Base):
	__tablename__ = "domains"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
	name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

	topics: Mapped[list["Topic"]] = relationship(
		back_populates="domain", cascade="all, delete-orphan"
	)


class Topic(Base):
	__tablename__ = "topics"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
	name: Mapped[str] = mapped_column(String, nullable=False)
	domain_id: Mapped[str] = mapped_column(
		String, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
	)

	domain: Mapped["Domain"] = relationship(back_populates="topics")
	subtopics: Mapped[list["Subtopic"]] = relationship(
		back_populates="topic", cascade="all, delete-orphan"
	)


class Subtopic(Base):
	__tablename__ = "subtopics"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
	name: Mapped[str] = mapped_column(String, nullable=False)
	topic_id: Mapped[str] = mapped_column(
		String, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
	)

	topic: Mapped["Topic"] = relationship(back_populates="subtopics")
	questions: Mapped[list["Question"]] = relationship(
		back_populates="subtopic", cascade="all, delete-orphan"
	)


class Question(Base):
	__tablename__ = "questions"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
	content: Mapped[str] = mapped_column(Text, nullable=False)
	difficulty: Mapped[QuestionDifficulty] = mapped_column(
		SAEnum(QuestionDifficulty), nullable=False
	)
	type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType), nullable=False)
	subtopic_id: Mapped[str] = mapped_column(
		String, ForeignKey("subtopics.id", ondelete="CASCADE"), nullable=False, index=True
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	subtopic: Mapped["Subtopic"] = relationship(back_populates="questions")
	versions: Mapped[list["QuestionVersion"]] = relationship(
		back_populates="question", cascade="all, delete-orphan"
	)


class QuestionVersion(Base):
	__tablename__ = "question_versions"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
	question_id: Mapped[str] = mapped_column(
		String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
	)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	model_answer: Mapped[str] = mapped_column(Text, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	question: Mapped["Question"] = relationship(back_populates="versions")
