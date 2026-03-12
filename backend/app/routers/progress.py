from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.session import InterviewSession, SessionStatus
from app.models.submission import CodeSubmission


router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full dashboard stats for the current user."""

    # Interview stats
    all_sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).all()

    completed = [s for s in all_sessions if s.status == SessionStatus.COMPLETED]
    scores = [s.overall_score for s in completed if s.overall_score is not None]

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    best_score = round(max(scores), 1) if scores else 0

    # Sessions by type
    by_type = {}
    for s in completed:
        t = s.interview_type.value
        by_type[t] = by_type.get(t, 0) + 1

    # Recent sessions (last 5)
    recent_sessions = sorted(completed, key=lambda x: x.started_at, reverse=True)[:5]

    # Code submission stats
    submissions = db.query(CodeSubmission).filter(
        CodeSubmission.user_id == current_user.id
    ).all()

    avg_code_quality = 0
    if submissions:
        quality_scores = [s.code_quality_score for s in submissions if s.code_quality_score]
        avg_code_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0

    # Score trend (last 10 sessions)
    score_trend = [
        {
            "date": s.started_at.strftime("%Y-%m-%d"),
            "score": s.overall_score,
            "type": s.interview_type.value,
        }
        for s in sorted(completed, key=lambda x: x.started_at)[-10:]
        if s.overall_score is not None
    ]

    return {
        "user": {
            "name": current_user.full_name,
            "target_role": current_user.target_role.value,
            "experience_level": current_user.experience_level.value,
        },
        "interview_stats": {
            "total_sessions": len(all_sessions),
            "completed_sessions": len(completed),
            "average_score": avg_score,
            "best_score": best_score,
            "sessions_by_type": by_type,
        },
        "coding_stats": {
            "total_submissions": len(submissions),
            "average_code_quality": avg_code_quality,
        },
        "score_trend": score_trend,
        "recent_sessions": [
            {
                "id": s.id,
                "type": s.interview_type.value,
                "role": s.target_role,
                "score": s.overall_score,
                "date": s.started_at.strftime("%Y-%m-%d"),
                "duration_seconds": s.duration_seconds,
            }
            for s in recent_sessions
        ],
    }


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full session history."""
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).all()

    return [
        {
            "id": s.id,
            "type": s.interview_type.value,
            "role": s.target_role,
            "difficulty": s.difficulty,
            "status": s.status.value,
            "score": s.overall_score,
            "summary": s.ai_summary,
            "strengths": s.strengths,
            "improvements": s.improvements,
            "date": s.started_at.strftime("%Y-%m-%d %H:%M"),
            "duration_seconds": s.duration_seconds,
        }
        for s in sessions
    ]