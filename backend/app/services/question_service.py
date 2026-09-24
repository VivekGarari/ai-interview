from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
    QuestionVersion,
    Subtopic,
)


def _coerce_difficulty(difficulty: QuestionDifficulty | str) -> QuestionDifficulty:
    try:
        return difficulty if isinstance(difficulty, QuestionDifficulty) else QuestionDifficulty(difficulty)
    except ValueError as exc:
        raise ValueError(f"Invalid question difficulty: {difficulty}") from exc


def _coerce_question_type(question_type: QuestionType | str) -> QuestionType:
    try:
        return question_type if isinstance(question_type, QuestionType) else QuestionType(question_type)
    except ValueError as exc:
        raise ValueError(f"Invalid question type: {question_type}") from exc


def create_question(
    db: Session,
    content: str,
    difficulty: QuestionDifficulty | str,
    question_type: QuestionType | str,
    subtopic_id: str,
    model_answer: Optional[str] = None,
) -> Question:
    """Create a persistent question and, optionally, its initial version."""
    subtopic = db.get(Subtopic, subtopic_id)
    if subtopic is None:
        raise ValueError(f"Subtopic not found: {subtopic_id}")

    question = Question(
        content=content,
        difficulty=_coerce_difficulty(difficulty),
        type=_coerce_question_type(question_type),
        subtopic=subtopic,
    )
    db.add(question)

    if model_answer is not None:
        question.versions.append(
            QuestionVersion(content=content, model_answer=model_answer)
        )

    db.commit()
    db.refresh(question)
    return question


def _filtered_questions_query(
    db: Session,
    topic_id: Optional[str] = None,
    difficulty: Optional[QuestionDifficulty | str] = None,
    question_type: Optional[QuestionType | str] = None,
):
    query = db.query(Question).join(Subtopic).filter(Subtopic.topic_id == topic_id) if topic_id else db.query(Question)

    if difficulty is not None:
        query = query.filter(Question.difficulty == _coerce_difficulty(difficulty))
    if question_type is not None:
        query = query.filter(Question.type == _coerce_question_type(question_type))

    return query


def get_questions_by_topic(
    db: Session,
    topic_id: str,
    difficulty: Optional[QuestionDifficulty | str] = None,
    question_type: Optional[QuestionType | str] = None,
) -> list[Question]:
    """Return questions assigned to subtopics under the requested topic."""
    return _filtered_questions_query(db, topic_id, difficulty, question_type).order_by(
        Question.created_at.asc(), Question.id.asc()
    ).all()


def get_random_question(
    db: Session,
    topic_id: Optional[str] = None,
    difficulty: Optional[QuestionDifficulty | str] = None,
    question_type: Optional[QuestionType | str] = None,
) -> Optional[Question]:
    """Return one randomly selected matching question, or None when unavailable."""
    return _filtered_questions_query(db, topic_id, difficulty, question_type).order_by(
        func.random()
    ).first()