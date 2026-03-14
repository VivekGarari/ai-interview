from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.session import InterviewSession, SessionQuestion, SessionStatus
from app.services.ai_service import ai_service
from app.schemas.interview import (
    StartSessionRequest, SubmitAnswerRequest, EndSessionRequest,
    SessionResponse, QuestionResponse, AnswerFeedbackResponse,
    FeedbackReportResponse, SessionDetailResponse,
)

router = APIRouter(prefix="/interview", tags=["Interview"])


# ── POST /interview/start ─────────────────────────────

@router.post("/start", response_model=dict)
def start_session(
    body: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new interview session and get the first question."""

    # Create session
    session = InterviewSession(
        user_id=current_user.id,
        interview_type=body.interview_type,
        target_role=body.target_role,
        difficulty=body.difficulty,
    )
    db.add(session)
    db.flush()

    # Generate first question via AI
    first_question_text = ai_service.generate_question(
        role=body.target_role,
        interview_type=body.interview_type.value,
        history=[],
        difficulty=body.difficulty,
    )

    # Save question to DB
    question = SessionQuestion(
        session_id=session.id,
        order_index=1,
        question_text=first_question_text,
    )
    db.add(question)
    db.commit()

    return {
        "session_id": session.id,
        "question": {
            "id": question.id,
            "question_text": question.question_text,
            "order_index": question.order_index,
        }
    }


# ── POST /interview/answer ────────────────────────────

@router.post("/answer", response_model=dict)
def submit_answer(
    body: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer, get AI feedback, and receive the next question."""

    # Verify session belongs to user
    session = db.query(InterviewSession).filter(
        InterviewSession.id == body.session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == SessionStatus.IN_PROGRESS,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already completed.")

    # Get the question being answered
    question = db.query(SessionQuestion).filter(
        SessionQuestion.id == body.question_id,
        SessionQuestion.session_id == body.session_id,
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Save answer
    question.answer_text = body.answer_text
    question.answered_at = datetime.now(timezone.utc)
    if body.response_time_seconds:
        question.response_time_seconds = body.response_time_seconds

    # AI evaluates the answer
    evaluation = ai_service.evaluate_answer(
        question=question.question_text,
        answer=body.answer_text,
        role=session.target_role,
        interview_type=session.interview_type.value,
    )

    question.score = evaluation["score"]
    question.ai_feedback = evaluation["feedback"]
    question.model_answer = evaluation.get("model_answer")
    question.follow_up_asked = evaluation["follow_up"]

    # Generate next question (max 5 questions per session)
    answered_count = db.query(SessionQuestion).filter(
        SessionQuestion.session_id == body.session_id,
        SessionQuestion.answer_text.isnot(None),
    ).count()

    next_question = None
    if answered_count < 5:
        # Get history of previous questions
        history = [q.question_text for q in db.query(SessionQuestion).filter(
            SessionQuestion.session_id == body.session_id
        ).all()]

        next_question_text = ai_service.generate_question(
            role=session.target_role,
            interview_type=session.interview_type.value,
            history=history,
            difficulty=session.difficulty,
        )

        next_q = SessionQuestion(
            session_id=session.id,
            order_index=answered_count + 2,
            question_text=next_question_text,
        )
        db.add(next_q)
        db.flush()
        next_question = {
            "id": next_q.id,
            "question_text": next_q.question_text,
            "order_index": next_q.order_index,
        }

    db.commit()

    return {
        "feedback": {
            "question_id": question.id,
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "follow_up": evaluation["follow_up"],
        },
        "next_question": next_question,
        "session_complete": next_question is None,
        "questions_answered": answered_count,
    }


# ── POST /interview/end ───────────────────────────────

@router.post("/end", response_model=FeedbackReportResponse)
def end_session(
    body: EndSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End the session and get a full AI feedback report."""

    session = db.query(InterviewSession).filter(
        InterviewSession.id == body.session_id,
        InterviewSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Get all answered questions
    questions = db.query(SessionQuestion).filter(
        SessionQuestion.session_id == body.session_id,
        SessionQuestion.answer_text.isnot(None),
    ).all()

    if not questions:
        raise HTTPException(status_code=400, detail="No answers to evaluate.")

    # Build session data for AI report
    session_data = {
        "interview_type": session.interview_type.value,
        "role": session.target_role,
        "questions": [
            {
                "question": q.question_text,
                "answer": q.answer_text,
                "score": q.score or 5.0,
            }
            for q in questions
        ],
    }

    # Generate full report
    report = ai_service.generate_feedback_report(session_data)

    # Save results to session
    session.status = SessionStatus.COMPLETED
    session.ended_at = datetime.now(timezone.utc)
    session.overall_score = report["overall_score"]
    session.ai_summary = report["summary"]
    session.strengths = report["strengths"]
    session.improvements = report["improvements"]

    if session.started_at:
        delta = datetime.now(timezone.utc) - session.started_at
        session.duration_seconds = int(delta.total_seconds())

    db.commit()

    avg_score = sum(q.score or 0 for q in questions) / len(questions)

    return FeedbackReportResponse(
        session_id=session.id,
        overall_score=report["overall_score"],
        summary=report["summary"],
        strengths=report["strengths"],
        improvements=report["improvements"],
        total_questions=len(questions),
        average_score=round(avg_score, 1),
    )


# ── GET /interview/sessions ───────────────────────────

@router.get("/sessions", response_model=list[SessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all interview sessions for the current user."""
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).all()
    return sessions


# ── GET /interview/session/{session_id} ───────────────

@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific session with all questions."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return session