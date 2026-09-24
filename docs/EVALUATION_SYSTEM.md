# Evaluation System — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Defines what "good evaluation" means for ProctoAI and how the current prototype does it
(and why that must change).

## 2. Non-negotiable principles

1. **Scores must be explainable.** Each score should trace to criteria and evidence.
2. **No single opaque AI number.** The system must not depend on one semantic-similarity score or
   one LLM-generated number for overall outcomes.
3. **The LLM evaluates against a known rubric**, it does not "generate truth".
4. **Deterministic checks happen first** (e.g., presence of expected concepts, coding test cases,
   keyword/structural checks) — only what cannot be checked deterministically goes to the LLM.
5. **Scores are aggregated deterministically** with stored weights.
6. **Reproducibility:** the original question, rubric, answer, prompt version and model must be
   retained so any evaluation can be replayed. Evaluations should eventually be replayable and
   versioned.

## 3. Target: conceptual evaluation object

```
{
  score: 0-10,                       # aggregate, deterministically derived
  per_criterion: [
    {
      criterion: "...",              # e.g. "technical correctness"
      weight: 0.3,
      score: 0-10,
      evidence: "..."                # pointer to excerpt / check results
    }
  ],
  strengths: [...],
  improvements: [...],
  concepts_covered: [...],
  concepts_missing: [...],
  model_answer_gap: "...",
  confidence: 0-1,
  needs_human_review: bool
}
```

Notes:

- `confidence` here expresses how confident the *system* is in its own evaluation (e.g., parse
  quality, rubric coverage) — not a claim about the candidate's personality/emotion.
- `needs_human_review` is the escape hatch for low-confidence or flagged evaluations.

## 4. Target: evaluation pipeline

```
Stored question
  → Expected concepts
    → Evaluation criteria + weights
      → Student answer
        → deterministic checks (concept presence, structure, test cases, …)
        → LLM evaluation against rubric (only what needs judgement)
        → structured evaluation record
          → deterministic aggregation (weighted, explainable)
            → stored result (+ prompt/model version for replay)
```

## 5. Target: candidate dimensions (overall level)

The final product should produce multiple dimensions rather than one opaque score `[FUTURE]`:

- technical knowledge
- conceptual depth
- problem solving
- coding
- communication
- interview performance
- answer quality
- consistency
- improvement over time

Each dimension is itself an aggregation of criteria. The overall "score" is a documented
combination of these dimensions — explainable because each layer has defined weights.

## 6. Current implementation reality

### Written interview (`evaluate_answer`) `[PARTIAL]`

- One LLM call with a text-format prompt (`SCORE:` / `FEEDBACK:` / `MODEL_ANSWER:` / `FOLLOW_UP:`).
- Line-by-line string parsing; silent `score=5.0` / `"Good attempt."` defaults on parse failure.
- `SessionQuestion.score` = that single LLM number. No rubric, no per-criterion breakdown,
  no evidence.

### Session report (`generate_feedback_report`) `[PARTIAL]`

- A *separate* LLM call produces `SUMMARY:` / `STRENGTHS:` / `IMPROVEMENTS:` / `OVERALL_SCORE:`
  from a re-serialized question list.
- Therefore `overall_score` (LLM) and `average_score` (computed column) are both returned and can
  disagree.

### Coding (`review_code`) `[PARTIAL]`

- LLM is asked for JSON `{score, correct, time_complexity, space_complexity, feedback,
  improvements}`. No test-case execution is integrated into grading (test fields are never
  populated), and `correct` is an unverified LLM boolean.

### Exam (`grade_exam_answer`) `[PARTIAL]`

- MCQs auto-graded deterministically (good). Short answers/coding are graded by a JSON-LLM call
  (`{score, feedback}`), scaled to points.

### Communication (video) `[PARTIAL]`

- WPM, filler-word rate, and pace are deterministic transcript heuristics (depends on
  transcription accuracy).
- "Confidence" is an LLM guess from transcript text via `video_service._analyze_confidence` —
  presented as `confidence_score`. Must be labelled as a heuristic/experimental, not a validated
  measure (see [Video Interview](VIDEO_INTERVIEW.md)).

## 7. What V1 must change (minimum)

1. Define a criteria schema per question type (concept question, coding problem, behavior/HR).
2. Persist the evaluation as structured data (`AnswerEvaluation`), not just a single score.
3. Deterministic aggregation for per-question and session-level scores; session overall =
   aggregation of per-question criteria, not a separate LLM call.
4. Store `question_id` (stored question, not raw text), answer, rubric, weights,
   `prompt_version`, `model` with every evaluation for replay.
5. Mark evaluations `needs_human_review` when parse confidence is low.

## 8. Open decisions

1. Which V1 criteria set + weights (propose: technical correctness, completeness, conceptual
   depth, clarity/structure — weights task-specific, e.g., coding emphasizes correctness; concept
   answers emphasize depth).
2. How strong the LLM's role is per criterion (e.g., LLM scores each criterion; app aggregates —
   recommended) vs fully deterministic keyword checks (too brittle).
3. When replay/versioning of evaluation runs ships (V1 vs early Phase 3).
4. Scale and interpretation: raw 0–10 per criterion, or rubrics with named levels
   (e.g. shallow/moderate/strong) — see Product Vision §5.1 for the mastery-direction.