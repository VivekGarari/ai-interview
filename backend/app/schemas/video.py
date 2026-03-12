from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StartVideoSessionRequest(BaseModel):
    interview_type: str = "behavioral"
    target_role: str = Field(min_length=2, max_length=100)
    difficulty: str = "medium"


class TranscribeRequest(BaseModel):
    session_id: str
    question_id: str
    duration_seconds: Optional[int] = None


class VideoAnswerFeedback(BaseModel):
    question_id: str
    transcript: str
    content_score: float
    content_feedback: str
    communication_score: float
    words_per_minute: int
    pace_feedback: str
    filler_words_found: dict
    filler_score: float
    confidence_score: float
    overall_score: float
    follow_up: Optional[str] = None
    next_question: Optional[dict] = None
    session_complete: bool = False


class VideoSessionReport(BaseModel):
    session_id: str
    overall_score: float
    content_score: float
    communication_score: float
    summary: str
    strengths: List[str]
    improvements: List[str]
    total_questions: int
    average_wpm: int
    total_filler_words: int
    recording_url: Optional[str] = None