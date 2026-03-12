import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.users import User
from app.services.ai_service import AIService
from app.schemas.exam import (
    ExamConfig, ExamStartResponse, ExamQuestion, ExamSubmission,
    ExamResult, QuestionResult, QuestionType, TimerMode
)

router = APIRouter(prefix="/exam", tags=["Mock Exam"])
ai_service = AIService()

# In-memory exam store (replace with Redis/DB for production)
_exams: dict = {}


def letter_grade(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    return "F"


@router.post("/start", response_model=ExamStartResponse)
def start_exam(
    config: ExamConfig,
    current_user: User = Depends(get_current_user),
):
    """Generate exam questions using AI and return exam session."""
    questions_raw = ai_service.generate_exam_questions(
        topic=config.topic,
        role=config.role,
        difficulty=config.difficulty,
        num_questions=config.num_questions,
        question_types=[qt.value for qt in config.question_types],
    )

    questions = []
    for i, q in enumerate(questions_raw):
        questions.append(ExamQuestion(
            id=i,
            type=q["type"],
            question=q["question"],
            options=q.get("options"),
            points=q.get("points", 2 if q["type"] == "coding" else 1),
        ))

    exam_id = str(uuid.uuid4())
    _exams[exam_id] = {
        "config": config.model_dump(),
        "questions": questions_raw,
        "user_id": current_user.id,
    }

    total_points = sum(q.points for q in questions)
    time_limit_seconds = config.time_limit_minutes * 60

    return ExamStartResponse(
        exam_id=exam_id,
        questions=questions,
        timer_mode=config.timer_mode,
        time_limit_seconds=time_limit_seconds,
        time_per_question_seconds=config.time_per_question_seconds if config.timer_mode == TimerMode.per_question else None,
        total_points=total_points,
    )


@router.post("/submit", response_model=ExamResult)
def submit_exam(
    submission: ExamSubmission,
    current_user: User = Depends(get_current_user),
):
    """Grade exam — auto for MCQ, AI for short answer and coding."""
    exam_data = _exams.get(submission.exam_id)
    if not exam_data:
        raise HTTPException(status_code=404, detail="Exam not found or expired")

    config = exam_data["config"]
    questions_raw = exam_data["questions"]
    answers_map = {a.question_id: a for a in submission.answers}

    question_results = []
    total_score = 0.0
    max_score = 0

    for i, q in enumerate(questions_raw):
        q_type = q["type"]
        answer_obj = answers_map.get(i)
        user_answer = answer_obj.answer.strip() if answer_obj else ""
        correct = q.get("correct_answer", "")
        points_possible = q.get("points", 2 if q_type == "coding" else 1)
        max_score += points_possible

        is_correct = False
        points_earned = 0
        ai_feedback = None

        if q_type == "mcq":
            is_correct = user_answer.strip().upper() == correct.strip().upper()
            points_earned = points_possible if is_correct else 0

        elif q_type in ("short_answer", "coding"):
            if user_answer:
                grade = ai_service.grade_exam_answer(
                    question=q["question"],
                    user_answer=user_answer,
                    correct_answer=correct,
                    question_type=q_type,
                    role=config["role"],
                )
                points_earned = round((grade["score"] / 10) * points_possible, 1)
                is_correct = grade["score"] >= 6
                ai_feedback = grade["feedback"]
            else:
                points_earned = 0
                ai_feedback = "No answer provided."

        total_score += points_earned
        question_results.append(QuestionResult(
            question_id=i,
            question=q["question"],
            type=q_type,
            your_answer=user_answer or "(no answer)",
            correct_answer=correct,
            is_correct=is_correct,
            points_earned=points_earned,
            points_possible=points_possible,
            ai_feedback=ai_feedback,
            explanation=q.get("explanation", ""),
        ))

    percentage = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
    grade = letter_grade(percentage)

    # Generate overall feedback
    summary = ai_service.generate_exam_summary(
        topic=config["topic"],
        role=config["role"],
        percentage=percentage,
        question_results=[{
            "question": r.question,
            "correct": r.is_correct,
            "type": r.type,
        } for r in question_results],
    )

    # Clean up
    del _exams[submission.exam_id]

    return ExamResult(
        exam_id=submission.exam_id,
        topic=config["topic"],
        role=config["role"],
        difficulty=config["difficulty"],
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        grade=grade,
        time_taken_seconds=submission.total_time_seconds or 0,
        question_results=question_results,
        strengths=summary.get("strengths", []),
        weaknesses=summary.get("weaknesses", []),
        recommendation=summary.get("recommendation", ""),
    )