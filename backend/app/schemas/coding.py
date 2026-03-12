from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request schemas ───────────────────────────────────

class RunCodeRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str = Field(min_length=1, max_length=30)
    problem_id: Optional[str] = None


class SubmitCodeRequest(BaseModel):
    problem_id: str
    code: str = Field(min_length=1)
    language: str = Field(min_length=1, max_length=30)


class GenerateProblemRequest(BaseModel):
    difficulty: str = "medium"
    topic: str = "arrays"


# ── Response schemas ──────────────────────────────────

class ProblemResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    topic: str
    examples: Optional[dict] = None
    constraints: Optional[str] = None
    hints: Optional[dict] = None
    is_ai_generated: bool

    model_config = {"from_attributes": True}


class RunCodeResponse(BaseModel):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    runtime_ms: Optional[int] = None
    success: bool


class SubmissionResponse(BaseModel):
    id: str
    problem_id: str
    language: str
    passed_tests: Optional[int] = None
    total_tests: Optional[int] = None
    runtime_ms: Optional[int] = None
    ai_review: Optional[str] = None
    code_quality_score: Optional[float] = None
    submitted_at: datetime

    model_config = {"from_attributes": True}