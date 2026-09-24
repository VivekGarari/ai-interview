# Product Roadmap — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]` — see
[PRODUCT_VISION](PRODUCT_VISION.md).

## 1. How to read this roadmap

This is the **current strategic roadmap**. It is a plan, not a promise. Phases are guides for
sequencing, not a rigid contract:

- Phases may be re-ordered, merged, or split as the product and the team learn.
- A phase marked "partially done" reflects what already exists in the codebase (which was built
  without this roadmap).
- The roadmap will evolve; update this document when it does.

## 2. Current state snapshot

The codebase already contains a working prototype that spans parts of Phases 1–7 out of order.
The roadmap below marks each phase with current status. Roughly:

- Phase 0 (definition): **in progress** — this documentation set is the first pass.
- Phase 1 (backend foundation): **partially implemented** (FastAPI, DB, JWT auth, basics) but
  missing migrations discipline, logging, rate limiting, and solid test infra.
- Phase 2 (knowledge/question system): **not implemented** — the single biggest missing piece
  between the prototype and V1.
- Phase 3 (written interview): **implemented** at a simple level (single-LLM) — needs rework for
  structured evaluation + controlled questions.
- Phase 4 (coding): **partially implemented**.
- Phase 5 (student profile): **not implemented** (only aggregate dashboard stats).
- Phase 6 (video): **partially implemented** (audio-only → transcript analysis).
- Phase 7 (frontend polish): **prototype exists**.
- Phase 8 (ProctoAI Hire): **not implemented**.
- Phase 9 (business infrastructure): **not implemented**.

## 3. Phases

### Phase 0 — Product definition + architecture + documentation
**Status: in progress ([V1] activity)**

- Product vision (done: [PRODUCT_VISION](PRODUCT_VISION.md)).
- V1 scope (done: [V1_SCOPE](V1_SCOPE.md)).
- Architecture + documentation set (done: this `docs/` directory).
- **Open decisions to resolve before Phase 1 implementation:** see the "Architectural decisions
  still open" list in [ARCHITECTURE](ARCHITECTURE.md#19-open-architectural-decisions).

### Phase 1 — Backend foundation
**Status: partial (`[PARTIAL]` — gaps marked below)**

| Item | Status |
|------|--------|
| Configuration | `[IMPLEMENTED]` — pydantic-settings (`app/core/config.py`) |
| Database | `[IMPLEMENTED]` — SQLAlchemy 2 sync + PostgreSQL |
| Authentication | `[IMPLEMENTED]` — JWT (access+refresh) + bcrypt; **needs hardening** (see [Security](SECURITY.md)) |
| Migrations | `[PARTIAL]` — alembic is a dependency but unused; columns added ad-hoc in `database.py` |
| Testing infrastructure | `[PARTIAL]` — `unittest`, only 2 small tests exist (`backend/tests/`) |
| Logging | `[NOT IMPLEMENTED]` |
| Rate limiting | `[NOT IMPLEMENTED]` — empty `app/middleware/rate_limiter.py` |
| API foundation | `[IMPLEMENTED]` — routers, `/health`, `/docs` |

### Phase 2 — Knowledge / question system
**Status: `[V1]` (not implemented)**

- Taxonomy (Domain → Topic → Subtopic → Skill/Concept → expected competencies).
- Question blueprint (versioned, structured).
- AI question generation bounded by taxonomy + requirements.
- Validation (schema + semantic), deduplication, persistence, question selection.
- See [Question System](QUESTION_SYSTEM.md).

### Phase 3 — Written interview
**Status: `[PARTIAL]` (prototype exists)**

- Sessions, answers, follow-ups: `[IMPLEMENTED]` (`/interview/*`, `/ws/interview/*`).
- Structured evaluation: `[V1]` (see [Evaluation System](EVALUATION_SYSTEM.md)).
- Adaptive questioning against a question store/rubric: `[V1]`.

### Phase 4 — Coding
**Status: `[PARTIAL]`**

- Problem generation/selection: `[PARTIAL]` (AI-generates each time; no controlled store).
- Secure execution: `[V1]` (current fallback executes Python locally on the backend host —
  see [Security](SECURITY.md) and [Coding System](CODING_SYSTEM.md)).
- Test cases: `[V1]` (fields exist in the model but are never populated/graded).
- Submission evaluation + code analysis: `[PARTIAL]` (AI text review only).

### Phase 5 — Student profile
**Status: `[V1]`/`[FUTURE]` (not implemented)**

- Skill tracking, mastery, weakness detection, progress, recommendations.
- See [Product Vision §5.1](PRODUCT_VISION.md).

### Phase 6 — Video interview
**Status: `[PARTIAL]` (audio-only)**

- Speech-to-text: `[IMPLEMENTED]` (Groq Whisper).
- Audio/video handling: `[PARTIAL]` (recordings saved locally; not served back).
- Communication analysis (pace/fillers): `[IMPLEMENTED]` (transcript heuristics).
- Structured interview evaluation: `[V1]`.
- Deferred out of V1 scope until written/coding/evaluation are reliable.
- See [Video Interview](VIDEO_INTERVIEW.md).

### Phase 7 — Frontend / product polish
**Status: `[PARTIAL]` (prototype pages exist)**

- Complete student experience, dashboard, interview UX, coding interface, video interface.
- See [Architecture §4](ARCHITECTURE.md#4-frontend-architecture-current).

### Phase 8 — ProctoAI Hire (company platform)
**Status: `[FUTURE]` (not implemented)**

- Companies, assessments, candidates, invitations, reports, company dashboard.
- See [Company Platform](COMPANY_PLATFORM.md).

### Phase 9 — Business infrastructure
**Status: `[FUTURE]` (not implemented)**

- Billing, subscriptions, organization management, analytics, internationalization, scaling.

## 4. Sequencing guidance

Recommended near-term order (unless the roadmap is revised):

1. Finish Phase 0 decisions.
2. Hardening of Phase 1 that is a prerequisite for everything: migrations, logging, rate
   limiting, security fixes, structured AI outputs.
3. Phase 2 (question system) — unlocks controlled interviews.
4. Phase 3 rework (structured evaluation on top of the question system).
5. Phase 4 coding (sandboxed execution + basic test-case grading).
6. Phase 5 seed (skill profile from written + coding results).
7. Phase 7 (frontend polish for the V1 flow, ProctoAI Interview Lab).
8. Phase 6 video only after the above is reliable.
9. Phase 8/9 are separate business bets, deliberately later.

## 5. Roadmap change policy

- Document any change to phase goals, ordering, or scope in this file (or reference the
  decision record).
- Keep [V1_SCOPE](V1_SCOPE.md) as the authoritative "what V1 ships" list.