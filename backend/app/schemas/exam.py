from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum


class QuestionType(str, Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    coding = "coding"


class TimerMode(str, Enum):
    fixed = "fixed"
    per_question = "per_question"


class ExamConfig(BaseModel):
    topic: str
    role: str
    difficulty: str = "medium"
    num_questions: int = Field(default=10, ge=3, le=30)
    question_types: List[QuestionType] = [QuestionType.mcq, QuestionType.short_answer]
    timer_mode: TimerMode = TimerMode.fixed
    time_limit_minutes: int = Field(default=20, ge=5, le=120)
    time_per_question_seconds: int = Field(default=90, ge=30, le=300)


class ExamQuestion(BaseModel):
    id: int
    type: QuestionType
    question: str
    options: Optional[List[str]] = None        # MCQ only
    correct_answer: Optional[str] = None       # filled after submission
    explanation: Optional[str] = None          # filled after submission
    points: int = 1


class ExamStartResponse(BaseModel):
    exam_id: str
    questions: List[ExamQuestion]
    timer_mode: TimerMode
    time_limit_seconds: int
    time_per_question_seconds: Optional[int]
    total_points: int


class QuestionAnswer(BaseModel):
    question_id: int
    answer: str
    time_taken_seconds: Optional[int] = None


class ExamSubmission(BaseModel):
    exam_id: str
    answers: List[QuestionAnswer]
    total_time_seconds: Optional[int] = None


class QuestionResult(BaseModel):
    question_id: int
    question: str
    type: QuestionType
    your_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: int
    points_possible: int
    ai_feedback: Optional[str] = None
    explanation: str


class ExamResult(BaseModel):
    exam_id: str
    topic: str
    role: str
    difficulty: str
    total_score: float
    max_score: int
    percentage: float
    grade: str
    time_taken_seconds: int
    question_results: List[QuestionResult]
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str