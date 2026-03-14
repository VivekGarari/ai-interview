from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.session import InterviewType, SessionStatus


# ── Request schemas ───────────────────────────────────

class StartSessionRequest(BaseModel):
    interview_type: InterviewType
    target_role: str = Field(min_length=2, max_length=100)
    difficulty: str = "medium"


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str = Field(min_length=1, max_length=5000)
    response_time_seconds: Optional[int] = None


class EndSessionRequest(BaseModel):
    session_id: str


# ── Response schemas ──────────────────────────────────

class QuestionResponse(BaseModel):
    id: str
    question_text: str
    order_index: int
    answer_text: Optional[str] = None
    score: Optional[float] = None
    ai_feedback: Optional[str] = None
    model_answer: Optional[str] = None
    follow_up_asked: Optional[str] = None

    model_config = {"from_attributes": True}


class AnswerFeedbackResponse(BaseModel):
    question_id: str
    score: float
    feedback: str
    follow_up: Optional[str] = None
    model_answer: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    interview_type: InterviewType
    target_role: str
    difficulty: str
    status: SessionStatus
    overall_score: Optional[float] = None
    ai_summary: Optional[str] = None
    strengths: Optional[list] = None
    improvements: Optional[list] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    questions: List[QuestionResponse] = []


class FeedbackReportResponse(BaseModel):
    session_id: str
    overall_score: float
    summary: str
    strengths: List[str]
    improvements: List[str]
    total_questions: int
    average_score: float