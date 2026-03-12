from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.submission import CodingProblem, CodeSubmission
from app.services.ai_service import ai_service
from app.services.code_runner import code_runner
from app.schemas.coding import (
    RunCodeRequest, RunCodeResponse,
    SubmitCodeRequest, SubmissionResponse,
    GenerateProblemRequest, ProblemResponse,
)

router = APIRouter(prefix="/coding", tags=["Coding"])


@router.get("/problems", response_model=list[ProblemResponse])
def get_problems(
    difficulty: str = None,
    topic: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CodingProblem)
    if difficulty:
        query = query.filter(CodingProblem.difficulty == difficulty)
    if topic:
        query = query.filter(CodingProblem.topic == topic)
    return query.all()


@router.post("/generate", response_model=ProblemResponse)
def generate_problem(
    body: GenerateProblemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = ai_service.generate_coding_problem(
        difficulty=body.difficulty,
        topic=body.topic,
        role=current_user.target_role.value,
    )
    problem = CodingProblem(
        title=result.get("title", "Coding Challenge"),
        description=result.get("description", ""),
        difficulty=body.difficulty,
        topic=body.topic,
        examples={"input": result.get("example_input", ""), "output": result.get("example_output", "")},
        constraints=result.get("constraints", ""),
        hints={"hint1": result.get("hint", "")},
        is_ai_generated=True,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@router.post("/run", response_model=RunCodeResponse)
def run_code(
    body: RunCodeRequest,
    current_user: User = Depends(get_current_user),
):
    result = code_runner.run(code=body.code, language=body.language)
    return RunCodeResponse(**result)


@router.post("/submit", response_model=SubmissionResponse)
def submit_code(
    body: SubmitCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == body.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")
    run_result = code_runner.run(code=body.code, language=body.language)
    review = ai_service.review_code(
        problem=problem.description,
        code=body.code,
        language=body.language,
    )
    submission = CodeSubmission(
        user_id=current_user.id,
        problem_id=body.problem_id,
        language=body.language,
        code=body.code,
        stdout=run_result.get("stdout"),
        stderr=run_result.get("stderr"),
        runtime_ms=run_result.get("runtime_ms"),
        ai_review=review.get("correctness", ""),
        code_quality_score=review.get("quality_score"),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/submissions", response_model=list[SubmissionResponse])
def get_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(CodeSubmission).filter(
        CodeSubmission.user_id == current_user.id
    ).order_by(CodeSubmission.submitted_at.desc()).all()