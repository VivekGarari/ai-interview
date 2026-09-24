# Interview System — ProctoAI (Written)

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Describes the **written AI interview** experience: what exists today and the intended
interviewer-style, adaptive probing target.

## 2. Target: the AI as interviewer (not a question list)

Conceptually:

```
Question
  → Student Answer
    → Evaluation
      → Follow-up Question
        → Deeper Follow-up
          → Further Evaluation
```

The examiner should behave like a real interviewer: when an answer is shallow, probe *why*,
*complexity*, *trade-offs*, *comparisons*; when it is strong, go deeper or move on. The system's
goal is to detect the difference between surface knowledge and conceptual depth.

## 3. Current implementation `[PARTIAL]`

### REST flow (`app/routers/interview.py`)

1. `POST /interview/start` — creates `InterviewSession`, calls `generate_question(...)` (fresh
   LLM question bounded only by role/type/difficulty), persists as `SessionQuestion` #1.
2. `POST /interview/answer` — verifies ownership (`session.user_id == current_user.id` and status
   `in_progress`), saves the answer, calls `evaluate_answer(...)`, stores `score`,
   `ai_feedback`, `model_answer`, `follow_up_asked`. Then, if fewer than 5 answered, calls
   `generate_question(...)` again with the question-text history and persists the next row.
3. `POST /interview/end` — collects answered questions, calls `generate_feedback_report(...)`,
   persists overall results, marks session completed.
4. `GET /interview/sessions`, `GET /interview/session/{id}` — history and detail.

### WebSocket flow (`app/routers/ws.py`)

- `WS /ws/interview/{session_id}` duplicates the same Q→answer→evaluate→next-Q loop with the same
  5-question cap. It shares the backend sync DB session; the AI call is blocking inside an async
  handler (event-loop impact).

### Characteristics worth noting

- The "follow-up" returned by `evaluate_answer` is persisted to `follow_up_asked` but is **not
  used** to generate the next question and is **not displayed** in the frontend — the current
  product does not actually probe.
- Next question generation is uncontrolled (no stored question bank, no rubric-driven selection).
- Session completeness and question caps are duplicated in three places (REST, WS, video).
- Type constraints: the backend enum supports `behavioral`, `technical`, `system_design`, `hr`,
  `coding`, `mixed`. The UI exposes the first four; `coding` interviews are not surfaced as
  written interviews (coding has its own product area).

### Frontend (`src/pages/InterviewPage.jsx`)

- Chat-style UI; config (type/role/difficulty); auto-ends at 5 questions (with an off-by-one quirk
  described in [Architecture §15](ARCHITECTURE.md#15-repository-audit)); shows AI feedback +
  score bar; final report modal links to history.

## 4. Target V1 behavior

1. Sessions reference **stored question versions** (see [Question System](QUESTION_SYSTEM.md)).
2. Follow-up behavior is real: the system determines gap areas from the answer/rubric and asks a
   targeted follow-up (one dedicated follow-up loop, max depth N).
3. Each answer produces a **structured evaluation** (see [Evaluation System](EVALUATION_SYSTEM.md)).
4. Question selection is **adaptive and deterministic**: rubric gaps + difficulty target +
   taxonomy constraints pick the next question; the LLM only drafts variations subject to
   validation.
5. One shared implementation behind both REST and (future) WS entry points.

## 5. V1 scope note

The V1 flow (Interview Lab) treats the written interview as the core modality
([V1_SCOPE](V1_SCOPE.md)) — with structure + evaluation; a "multi-stage" written interview
(multiple rubrics per session, e.g. concept → code → explanation) is a `[FUTURE]` refinement.

## 6. Open decisions

1. Max depth/follow-ups per question in V1 (recommend 1–2).
2. WS vs REST as the single path for V1 (recommend REST first; revisit WS later).
3. Whether the video modality reuses the same session/evaluation core (yes, recommended).