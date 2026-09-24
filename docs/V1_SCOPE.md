# V1 Scope — ProctoAI Interview Lab

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]` — see
[PRODUCT_VISION](PRODUCT_VISION.md).

V1 is intentionally small. It is designed to prove one central hypothesis:

> **Can ProctoAI help students identify and improve the gap between what they know and how well
> they can perform in an interview?**

Do not build the entire long-term vision in V1.

---

## 1. V1 product shape (recommended)

**ProctoAI Interview Lab** — a single, connected preparation flow.

### 1.1 Student configuration

The student selects:

- role / domain
- language where applicable
- topic / skill
- difficulty

### 1.2 The V1 journey

```
Concept / knowledge practice
        ↓
AI written interview
        ↓
Follow-up questions
        ↓
Structured evaluation
        ↓
Coding challenge
        ↓
Coding evaluation
        ↓
Personalized report
```

The stages above are **connected**: the concepts practiced inform the interview; interview
weaknesses inform the coding challenge; both feed the personalized report.

## 2. What V1 must provide (functional requirements)

| # | Requirement | Status today |
|---|-------------|--------------|
| 1 | Student can select role/domain + topic/skill + difficulty | `[PARTIAL]` — role/difficulty exist; no controlled topic taxonomy for interviews |
| 2 | Concept/knowledge practice module (structured, taxonomy-backed) | `[V1]` — **not built** |
| 3 | AI written interview with adaptive follow-up questioning | `[PARTIAL]` — see [Interview System](INTERVIEW_SYSTEM.md) |
| 4 | Structured per-answer evaluation (deterministic aggregation, not a single LLM number) | `[V1]` — **not built** (current: single LLM score) |
| 5 | Coding challenge with secure execution + basic grading | `[PARTIAL]` — AI generation + run + text review; no test-case grading |
| 6 | Personalized end-of-session report | `[PARTIAL]` — report exists but is LLM-generated prose |
| 7 | Progress persistence (sessions, answers, scores in DB) | `[IMPLEMENTED]` |
| 8 | Student dashboard/history | `[IMPLEMENTED]` at aggregate level |
| 9 | Reliable evaluation foundation before any video feature | Principle — video is **deferred** out of V1 |

## 3. In scope (V1)

- The student learning/preparation product (ProctoAI Learn).
- A controlled **question/taxonomy system** (see [Question System](QUESTION_SYSTEM.md)) so that
  interviews are not powered by one-off unvalidated LLM prompts.
- A **provider-abstraction layer** for LLM calls with structured outputs (see
  [AI System](AI_SYSTEM.md)); OpenRouter intended as primary general provider, Groq for
  speech-related workloads.
- Written interview + follow-ups + structured evaluation.
- Basic **coding challenge** flow: select/generate, run safely in a sandbox, evaluate against
  test cases where feasible, basic code-quality feedback.
- Personalized report derived from structured evaluation components.
- Progress tracking per concept/topic (seed of the skill profile).
- Core security hardening (see [Security](SECURITY.md)): prompt-injection resistance,
  structured AI outputs, secure code execution, rate limiting, file-upload validation.

## 4. Explicitly OUT of scope for V1

The following belong to later phases. Do **not** creep them into V1:

- Company hiring platform (ProctoAI Hire)
- Payments / billing / subscriptions
- Full LMS (course authoring, grading rubrics UI, etc.)
- Resume / ATS system
- Advanced avatar / lip-sync interviewer
- Complex emotion detection, eye tracking, psychological inference
- Multi-tenancy, enterprise SSO, org management
- Advanced analytics
- Large-scale social features
- Microservices architecture
- Massive question marketplace
- Video interviewing *(introduced only after the written/coding/evaluation foundation is
  reliable)*

## 5. Definition of done for V1

V1 is complete when a student can:

1. Select a role + topic + difficulty.
2. Study/practice the concept with structured material.
3. Sit an AI written interview that probes weak understanding.
4. Receive per-question structured feedback and a session report that is explainable
   (derived from criteria, not "the AI said 6.8").
5. Attempt a coding challenge, have it executed safely and evaluated.
6. See, in one report, their strengths, weaknesses, and what to practice next.
7. Repeat and observe change over time in the dashboard.

## 6. Explicit non-goal for the V1 report

The V1 report must **not** depend on a single semantic-similarity score or a single LLM-generated
number. Multi-dimension output (technical knowledge, conceptual depth, communication, coding,
consistency, improvement) is `[FUTURE]`; V1 should at minimum make each per-criterion score
traceable to evidence.