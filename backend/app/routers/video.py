from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.session import InterviewSession, SessionQuestion, SessionStatus, InterviewType
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
from app.services.stt_services import stt_service
from app.services.video_service import video_analysis_service
from app.schemas.video import (
    StartVideoSessionRequest,
    VideoAnswerFeedback,
    VideoSessionReport,
)

router = APIRouter(prefix="/video", tags=["Video Interview"])

# Local storage path for recordings (swap for S3 in production)
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)


# ── POST /video/start ─────────────────────────────────

@router.post("/start")
def start_video_session(
    body: StartVideoSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a video interview session.
    Returns: session_id, first question text, and TTS audio URL.
    """
    session = InterviewSession(
        user_id=current_user.id,
        interview_type=InterviewType(body.interview_type),
        target_role=body.target_role,
        difficulty=body.difficulty,
    )
    db.add(session)
    db.flush()

    # Generate first question
    question_text = ai_service.generate_question(
        role=body.target_role,
        interview_type=body.interview_type,
        history=[],
        difficulty=body.difficulty,
    )

    question = SessionQuestion(
        session_id=session.id,
        order_index=1,
        question_text=question_text,
    )
    db.add(question)
    db.commit()

    return {
        "session_id": session.id,
        "question": {
            "id": question.id,
            "text": question.question_text,
            "order_index": question.order_index,
            "audio_url": f"/video/question/{question.id}/audio",
        },
        "avatar": {
            "voice_enabled": tts_service.enabled,
            "voice_id": tts_service.INTERVIEWER_VOICE_ID,
        }
    }


# ── GET /video/question/{question_id}/audio ───────────

@router.get("/question/{question_id}/audio")
def get_question_audio(
    question_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns MP3 audio of the AI interviewer speaking the question.
    Frontend plays this to simulate AI avatar speaking.
    """
    question = db.query(SessionQuestion).filter(
        SessionQuestion.id == question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    audio_bytes = tts_service.get_question_audio(question.question_text)

    if not audio_bytes:
        raise HTTPException(
            status_code=503,
            detail="TTS not configured. Add ELEVENLABS_API_KEY to .env to enable voice."
        )

    return Response(content=audio_bytes, media_type="audio/mpeg")


# ── POST /video/transcribe ────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(
    session_id: str = Form(...),
    question_id: str = Form(...),
    duration_seconds: int = Form(default=0),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receives mic audio, transcribes it via Groq Whisper,
    evaluates the answer with AI, and returns full feedback.
    """
    # Verify session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
        InterviewSession.status == SessionStatus.IN_PROGRESS,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    question = db.query(SessionQuestion).filter(
        SessionQuestion.id == question_id,
        SessionQuestion.session_id == session_id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Read audio and transcribe
    audio_bytes = await audio.read()
    stt_result = stt_service.transcribe(audio_bytes, filename=audio.filename or "audio.webm")

    if not stt_result["success"] or not stt_result["transcript"]:
        raise HTTPException(
            status_code=422,
            detail=f"Could not transcribe audio: {stt_result.get('error', 'Unknown error')}"
        )

    transcript = stt_result["transcript"]
    audio_duration = stt_result.get("duration") or duration_seconds

    # Save transcript as the answer
    question.answer_text = transcript
    question.answered_at = datetime.now(timezone.utc)
    question.response_time_seconds = int(audio_duration)

    # AI evaluates content of the answer
    content_eval = ai_service.evaluate_answer(
        question=question.question_text,
        answer=transcript,
        role=session.target_role,
        interview_type=session.interview_type.value,
    )

    # Analyze communication quality (pace, fillers, confidence)
    comm_analysis = video_analysis_service.analyze_transcript(
        transcript=transcript,
        duration_seconds=int(audio_duration),
    )

    # Save scores
    question.score = content_eval["score"]
    question.ai_feedback = content_eval["feedback"]

    # Overall score = 60% content + 40% communication
    overall = round(
        (content_eval["score"] * 0.6) + (comm_analysis["overall_communication_score"] * 0.4), 1
    )

    # Check how many questions answered
    answered_count = db.query(SessionQuestion).filter(
        SessionQuestion.session_id == session_id,
        SessionQuestion.answer_text.isnot(None),
    ).count()

    # Generate next question (max 5)
    next_question = None
    if answered_count < 5:
        history = [q.question_text for q in db.query(SessionQuestion).filter(
            SessionQuestion.session_id == session_id
        ).all()]

        next_q_text = ai_service.generate_question(
            role=session.target_role,
            interview_type=session.interview_type.value,
            history=history,
            difficulty=session.difficulty,
        )
        next_q = SessionQuestion(
            session_id=session.id,
            order_index=answered_count + 2,
            question_text=next_q_text,
        )
        db.add(next_q)
        db.flush()
        next_question = {
            "id": next_q.id,
            "text": next_q.question_text,
            "order_index": next_q.order_index,
            "audio_url": f"/video/question/{next_q.id}/audio",
        }

    db.commit()

    return VideoAnswerFeedback(
        question_id=question.id,
        transcript=transcript,
        content_score=content_eval["score"],
        content_feedback=content_eval["feedback"],
        communication_score=comm_analysis["overall_communication_score"],
        words_per_minute=comm_analysis["words_per_minute"],
        pace_feedback=comm_analysis["pace_feedback"],
        filler_words_found=comm_analysis["filler_words_found"],
        filler_score=comm_analysis["filler_score"],
        confidence_score=comm_analysis["confidence_score"],
        overall_score=overall,
        follow_up=content_eval.get("follow_up"),
        next_question=next_question,
        session_complete=next_question is None,
    )


# ── POST /video/upload-recording ──────────────────────

@router.post("/upload-recording")
async def upload_recording(
    session_id: str = Form(...),
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload the full session recording.
    Saves locally (swap for S3 in production).
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Save file locally
    filename = f"{session_id}_{uuid.uuid4().hex[:8]}.webm"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    contents = await video.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Save recording URL to session
    recording_url = f"/video/recording/{filename}"
    session.recording_url = recording_url if hasattr(session, 'recording_url') else None
    db.commit()

    return {
        "success": True,
        "recording_url": recording_url,
        "filename": filename,
        "size_bytes": len(contents),
    }


# ── POST /video/end ───────────────────────────────────

@router.post("/end", response_model=VideoSessionReport)
def end_video_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    End session and generate full video interview report including
    content scores + communication analysis.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = db.query(SessionQuestion).filter(
        SessionQuestion.session_id == session_id,
        SessionQuestion.answer_text.isnot(None),
    ).all()

    if not questions:
        raise HTTPException(status_code=400, detail="No answers to evaluate.")

    # Aggregate communication metrics
    total_wpm = 0
    total_fillers = 0
    comm_scores = []

    for q in questions:
        if q.answer_text and q.response_time_seconds:
            analysis = video_analysis_service.analyze_transcript(
                transcript=q.answer_text,
                duration_seconds=q.response_time_seconds,
            )
            total_wpm += analysis["words_per_minute"]
            total_fillers += analysis["filler_word_count"]
            comm_scores.append(analysis["overall_communication_score"])

    avg_wpm = total_wpm // len(questions) if questions else 0
    avg_comm = sum(comm_scores) / len(comm_scores) if comm_scores else 5.0

    # AI generates overall content report
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
    report = ai_service.generate_feedback_report(session_data)

    # Combined score: 60% content + 40% communication
    content_score = report["overall_score"]
    overall = round((content_score * 0.6) + (avg_comm * 0.4), 1)

    # Save to DB
    session.status = SessionStatus.COMPLETED
    session.ended_at = datetime.now(timezone.utc)
    session.overall_score = overall
    session.ai_summary = report["summary"]
    session.strengths = report["strengths"]
    session.improvements = report["improvements"]

    if session.started_at:
        delta = datetime.now(timezone.utc) - session.started_at
        session.duration_seconds = int(delta.total_seconds())

    db.commit()

    return VideoSessionReport(
        session_id=session.id,
        overall_score=overall,
        content_score=content_score,
        communication_score=round(avg_comm, 1),
        summary=report["summary"],
        strengths=report["strengths"],
        improvements=report["improvements"],
        total_questions=len(questions),
        average_wpm=avg_wpm,
        total_filler_words=total_fillers,
    )