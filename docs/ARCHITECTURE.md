# Architecture — ProctoAI

This document describes the **current** architecture of the repository and the **target**
architecture the product is intended to move toward. It explicitly separates `CURRENT CODE` from
`TARGET ARCHITECTURE`.

## Status legend

Used across the whole `docs/` tree:

| Label | Meaning |
|-------|---------|
| `[IMPLEMENTED]` | Exists in the current codebase and is reachable through the app |
| `[PARTIAL]` | A real feature exists but is incomplete, fragile, or divergent from the target contract |
| `[V1]` | Explicitly planned for the near-term V1 build (ProctoAI Interview Lab). Not built unless noted |
| `[FUTURE]` | Long-term planned capability. Not built |
| `[IDEA]` | Noted possibility, no commitment |

**Rule:** never describe a `[V1]`/`[FUTURE]`/`[IDEA]` item as if it exists.

---

## 1. Current architecture — overview

```
Browser (React SPA) ──HTTP/WS──► FastAPI ──► PostgreSQL (Render)
   ^                                  │
   │                                  ├── Groq (LLM: llama-3.3-70b-versatile)
   │                                  ├── Groq Whisper (STT)
   │                                  ├── Edge TTS (interviewer voice)
   │                                  ├── Resend (email)
   │                                  └── Judge0 / local subprocess (code run)
```

- **Backend:** FastAPI `0.115.6`, Python `3.11.9`, sync SQLAlchemy 2 + psycopg2, PostgreSQL.
  Deployed on Render (`Procfile`, `runtime.txt`).
- **Frontend:** React `19` + Vite `7` + Tailwind `3`, zustand, axios, react-router `7`.
  Deployed as a static site (`public/_redirects` suggests a static host; exact host not documented).
- **AI:** all LLM work currently goes to **Groq** through `app/services/ai_service.py`.
- **Auth:** JWT (access + refresh), bcrypt password hashing, `HTTPBearer`.
- **Code execution:** `app/services/code_runner.py` — Judge0 if an API key is configured,
  otherwise **local Python subprocess** (see [Security](SECURITY.md) — this is a risk).

## 2. Backend structure (current)

```
backend/app/
├── main.py            # FastAPI app, CORS, lifespan (create_tables + add_model_answer_column)
├── core/
│   ├── config.py      # pydantic-settings (env vars; provider fields added, uncommitted WIP)
│   ├── database.py    # engine, session factory, Base, ad-hoc migration helpers
│   └── security.py    # hash_password, JWT encode/decode, get_current_user
├── models/
│   ├── users.py       # User
│   ├── session.py     # InterviewSession, SessionQuestion, enums
│   ├── submission.py  # CodingProblem, CodeSubmission
│   ├── question.py    # <empty stub> — planned Question entity, not implemented
│   └── __init__.py    # imports models so Base.metadata sees them
├── schemas/           # Pydantic request/response models (auth, interview, coding, video, exam)
├── routers/
│   ├── auth.py        # signup/login/refresh/me/change-password/logout/verify-email/resend-otp/reset-password-temp
│   ├── interview.py   # written interview: start/answer/end/sessions/session
│   ├── ws.py          # WebSocket clone of the written interview
│   ├── video.py       # video interview: start/transcribe/upload-recording/end + question audio
│   ├── coding.py      # problems/generate/run/submit/submissions
│   ├── exam.py        # mock exam: start/submit (AI-generated questions, in-memory store)
│   ├── progress.py    # dashboard + history aggregates
│   ├── ai.py          # <untracked WIP> /ai/capabilities + /ai/route (cosmetic provider routing)
│   └── (middleware/)  # auth_middleware.py, rate_limiter.py — <empty stubs>
└── services/
    ├── ai_service.py  # ALL Groq calls (question gen, evaluate, reports, coding, exam, resume)
    ├── orchestrator.py # <untracked WIP> ProviderConfig/AIOrchestrator (capability routing concept)
    ├── code_runner.py # Judge0 / local python execution
    ├── video_service.py # transcript analysis (WPM, fillers, pace, text-based "confidence")
    ├── stt_services.py # Groq Whisper transcription
    ├── tts_service.py  # Edge TTS
    ├── email_service.py # Resend OTP email
    └── feedback_service.py # <empty stub>
```

Note: files marked "untracked WIP" exist in the working tree but are not yet committed
(`routers/ai.py`, `services/orchestrator.py`, `tests/`).

## 3. Backend API inventory (current, committed)

| Area | Method & path | Notes |
|------|---------------|-------|
| Health | `GET /health` | also answers `HEAD` |
| Authed | `GET /docs`, `GET /redoc` | Swagger/ReDoc |
| Auth | `POST /auth/signup` | **creates user already verified** (`is_verified=True`) |
| | `POST /auth/login` | issues access+refresh |
| | `POST /auth/refresh` | refreshes both tokens (stateless) |
| | `GET /auth/me`, `PATCH /auth/me` | profile read/update |
| | `POST /auth/change-password` | authenticated |
| | `POST /auth/logout` | stateless (no revocation) |
| | `POST /auth/verify-email`, `POST /auth/resend-otp` | OTP flow exists but signup bypasses it |
| | `POST /auth/reset-password-temp` | **NO AUTH — critical: remove** (see [Security](SECURITY.md)) |
| Interview | `POST /interview/start` | creates session + generates Q1 via LLM |
| | `POST /interview/answer` | saves answer, LLM evaluates, generates next Q (max 5) |
| | `POST /interview/end` | LLM generates final report, persists |
| | `GET /interview/sessions`, `GET /interview/session/{id}` | history |
| WebSocket | `WS /ws/interview/{session_id}` | live alternative to the REST interview flow |
| Video | `POST /video/start` | session + question + TTS flag |
| | `GET /video/question/{id}/audio` | Edge TTS MP3 (**unauth**) |
| | `POST /video/transcribe` | audio upload → Whisper → evaluate + comm analysis |
| | `POST /video/upload-recording` | saves webm to local disk; URL is dead (no GET route) |
| | `POST /video/end` | final report (content 60% + communication 40%) |
| Coding | `GET /coding/problems` | filters: difficulty, topic |
| | `POST /coding/generate` | LLM generates & persists a CodingProblem |
| | `POST /coding/run` | executes code (Judge0 or local) |
| | `POST /coding/submit` | run + LLM code review, persists submission |
| | `GET /coding/submissions` | user submissions |
| Exam | `POST /exam/start` | LLM generates MCQ/short-answer/coding exam; **stored in-memory** |
| | `POST /exam/submit` | auto-grades MCQ, LLM-grades short answers/coding, LLM summary |
| Progress | `GET /progress/dashboard` | session/coding aggregates |
| | `GET /progress/history` | session list with summary/strengths/weaknesses |
| AI (WIP, untracked) | `GET /ai/capabilities`, `POST /ai/route` | provider routing concept; **not wired to real provider switching** |

## 4. Frontend architecture (current)

- SPA with routes: `/login`, `/signup`, `/verify-email`, and an authed layout with
  `/` (dashboard), `/interview` (Concept Review), `/video-interview`, `/coding`,
  `/history`, `/exam`, `/settings`.
- `src/services/api.js` — axios client. **Hardcodes the production backend**
  (`https://proctoai-backend.onrender.com`); attaches Bearer token from `localStorage`;
  auto-refresh on 401.
- `src/store/authStore.js` — zustand store (init via `/auth/me`, login/signup/logout).
- `src/data/options.js` — frontend-only "taxonomy" of roles, experience levels, coding topics,
  interview types. **Not shared with the backend** (backend accepts free-text roles).
- Pages: `InterviewPage` (chat-style written interview), `VideoInterviewPage`
  (camera + audio recording → transcribe), `CodingPage` (editor + run + AI review),
  `MockExamPage` (timed MCQ/short-answer/coding exam), `HistoryPage`, `DashboardPage`,
  `SettingsPage`, auth pages.
- No routing guard for unverified users beyond `PrivateRoute` redirecting to `/verify-email`
  (which is effectively never needed because signup sets `is_verified=True`).

### Known frontend problems (see also §15 audit)

1. `VideoInterviewPage` uses browser APIs that are **not standard in mainstream browsers**
   (`navigator.mediaDevices.getUserMedia`, `MediaRecorder`, `recorder.ondataavailable`). This
   feature should be assumed non-functional in production until verified against real browsers.
2. `src/services/api.js` defines `resumeAPI.analyze` (→ `POST /resume/analyze`) but **no backend
   endpoint exists** — dead code.
3. `options.js` lists `case_study` and `domain` interview types that the backend enum rejects
   (`InterviewType` has no such values). Not currently reachable from the UI.
4. `InterviewPage` ends a session when the backend reports `questions_answered >= 4`, so a
   generated 5th question may be created but never displayed (off-by-one between UI count and
   backend count).
5. Leftover Vite template files (`src/App.css`, `src/assets/react.svg`) are unused.

## 5. Target architecture — overview

```
Student SPA (React) ──HTTP/WS──► ProctoAI API (FastAPI, modular)
                                   ├── Auth & users
                                   ├── Question System        (taxonomy → generation → validation → dedup → persistence → selection)
                                   ├── Interview Engine       (written / coding / video sessions, adaptive probing)
                                   ├── Evaluation Engine      (deterministic aggregation over criteria; LLM assists rubrics only)
                                   ├── Skill Profile          (mastery, weakness detection, recommendations)
                                   ├── LLM Interface          (provider abstraction; structured outputs; retries/timeouts; prompt versioning)
                                   │     ├── OpenRouter (target: primary general LLM)
                                   │     ├── Groq       (target: speech/specialized; STT today)
                                   │     └── future providers
                                   └── (future, separate) ProctoAI Hire — companies/assessments
```

### 5.1 Mandated architectural principles (target)

1. **The LLM is not the source of truth.** Schema-validate, then semantics-validate, then persist.
2. **Single provider abstraction** — do not hard-code one provider across services. OpenRouter is
   the intended primary general-purpose provider; Groq remains useful for speech workloads. Do
   not build a complex dynamic capability-routing system without a real requirement.
3. **Structured outputs, JSON schema validation, retries, timeouts, prompt versioning, model and
   provider configuration.** Deterministic application-side logic where possible.
4. **No global semantic-similarity score.** Evaluation is criteria-based and explainable.
5. **Secure by default** (see [Security](SECURITY.md)) — never run untrusted code on the backend
   host; never trust LLM output as application data.
6. **Student and company products stay separated** (ProctoAI Learn vs ProctoAI Hire), sharing
   only core infrastructure.
7. **Monolith-first.** No microservices. Scale by improving the architecture of one service.

## 6. Target backend module layout (proposed)

```
app/
├── core/              # config, db, security, logging, rate limiting, errors
├── db/                # migrations (alembic), Base
├── domains/
│   ├── auth/          # users, tokens
│   ├── taxonomy/      # Domain/Topic/Subtopic/Skill + competencies
│   ├── questions/     # blueprint, generation, validation, dedup, selection
│   ├── interviews/    # sessions, answers, follow-ups (written)
│   ├── coding/        # problems, sandbox runner, test cases
│   ├── video/         # stt/tts, audio handling, communication analysis
│   ├── evaluation/    # criteria, rubrics, aggregation, replay
│   └── profile/       # mastery, weakness detection, recommendations
├── providers/         # LLM provider adapters (openrouter, groq, ...)
├── api/               # HTTP routers per domain
└── infra/             # background jobs, object storage, notifications
```

Domain-driven but pragmatic: **do not** restructure the codebase into this layout until V1 work
actually begins. This is the target, not today.

## 7. Current vs target — per component

| Component | Current | Target |
|-----------|---------|--------|
| Questions | AI regenerates free text each session; persisted only as `SessionQuestion.question_text` | Question blueprint store; versioned, validated, deduplicated; sessions reference stored questions |
| Evaluation | Single LLM call → score 0–10 + text; report from separate LLM call | Criteria + weights; deterministic aggregation; evidence; replayable/versioned; reproduce from stored question/rubric/answer |
| Interview | Linear: Q → answer → score → next Q (fresh). Follow-up is an unused text field | Adaptive probing: follow-ups derived from previous answers and rubric gaps |
| Coding | AI-generated problem; local candidate-code execution removed; fails safely when Judge0
  is unavailable; Judge0 sandbox path preserved | Controlled problem store; sandboxed execution
  (Judge0/isolate); test-case grading; complexity + quality + reasoning evaluation; feeds skill profile |
| Video | Audio → Whisper → content eval + transcript heuristics (WPM, fillers, pace, "confidence") | Structured interview evaluation; ethical communication metrics; deferred out of V1 |
| Roles/topics | Frontend hard-coded lists + free-text backend fields | Backend-authoritative taxonomy used by both products |
| Auth | JWT in localStorage; no revocation; reset-password-temp endpoint removed | Hardened auth; scoped per
  product (Learn vs Hire); optional SSO later; temp reset endpoint removed |
| AI routing | Groq hard-coded; cosmetic `/ai/*` routing concept | Provider adapters; OpenRouter primary; structured outputs |
| Data | One PostgreSQL DB; ad-hoc migrations | Alembic migrations; separated conceptual areas (see [Data Model](DATA_MODEL.md)) |

## 8. Current vs target — AI call flow

**Question generation — target:**

```
Taxonomy → Question requirements → LLM generation → Schema validation → Semantic validation
        → Deduplication → Persistence → Question becomes usable
```

**Question generation — current:** `generate_question()` (ai_service.py) sends a prompt with role,
type, difficulty, and recent history; returns raw text. No validation, no dedup, no persistence
as a reusable entity.

**Evaluation — target:**

```
Stored question → Expected concepts → Evaluation criteria → Student answer
        → LLM evaluation (against rubric) → Structured evaluation → Deterministic aggregation → Stored result
```

**Evaluation — current:** `evaluate_answer()` asks the LLM for a `SCORE:/FEEDBACK:/MODEL_ANSWER:/
FOLLOW_UP:` text block and parses it line by line with string parsing and a silent default of
5.0 on parse failure. Session overall score is a separate LLM number.

## 9. Concurrency / runtime model (current)

- All routers are **synchronous**; FastAPI runs them in a thread pool.
- `ai_service`, `stt_service`, `tts_service` make blocking network calls.
- `ws.py` uses a synchronous `SessionLocal()` inside an async WebSocket handler — this blocks the
  event loop during AI calls. Works at prototype scale; must be redesigned for V1.
- `exam.py` stores exams in a module-level dict (`_exams`) — lost on restart and not shared
  across multiple workers/instances. Clearly marked as "replace with Redis/DB."

## 10. Database (current)

- Tables: `users`, `interview_sessions`, `session_questions`, `coding_problems`,
  `code_submissions`.
- Auto-created via `Base.metadata.create_all()` on startup; ad-hoc `ALTER TABLE` helpers for a few
  columns. **No alembic migration history** despite alembic being a dependency.
- See [Data Model](DATA_MODEL.md) for full field-level detail.

## 11. Deployment (current)

- **Backend:** Render web service, root dir `backend/`, start command from `Procfile`
  (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`), Python 3.11.9 (`runtime.txt`).
  Free tier spins down after inactivity (README suggests UptimeRobot).
- **Database:** Render-managed PostgreSQL; `DATABASE_URL` env var. Redis is configured
  (`REDIS_URL`) but **not used** anywhere.
- **Frontend:** static site; `frontend/public/_redirects` (`/*  /index.html  200`). Exact host
  (Netlify/Cloudflare/others) is not documented in the repo. `api.js` points at the Render backend.
- `docker-compose.yml` provides local PostgreSQL (with a **hardcoded password** — see
  [Security](SECURITY.md)) and Redis.
- **Secrets:** `.env` is gitignored; keys live in Render env vars. The uncommitted `.env` file
  must not be committed.

## 12. Testing (current)

- Framework: Python `unittest` (stdlib).
- Coverage: only `backend/tests/test_ai_router.py` and `test_orchestrator.py` (new, untracked WIP)
  — machine tests of the cosmetic routing code.
- No tests for auth, interview, coding, video, exam, progress, or DB layers.
- No frontend tests, no lint CI, no test CI.

## 13. Logging / observability (current)

- Print-based logging only (`print(...)` in lifespan, migrations, email failure).
- No request logging, no error tracking, no metrics, no structured logs.

## 14. Security posture (current)

Highlights only — the full register is in [Security](SECURITY.md):

- Critical: reset-password-temp endpoint removed; no unauthenticated password reset currently exists.
- Critical: local candidate-code execution removed; no reachable path to subprocess.run/os.system/exec/eval/direct Python execution for candidate code.
- High: JWT access + refresh tokens stored in `localStorage` (XSS exposure); logout is stateless;
  refresh tokens never rotate/revoke.
- High: no rate limiting on auth or AI endpoints (cost + abuse); OTP brute-force (6-digit, no
  attempt cap).
- High: prompt-injection surface — user answers are interpolated into prompt templates.
- Medium: unbounded file uploads (`/video/transcribe`, `/video/upload-recording`) with no content
  validation; recordings accumulate on disk.
- Medium: unverified-LMX/false claims — the video "confidence" score is an LLM guess from
  transcript text.
- Medium: `docker-compose.yml` commits a DB password in plain text.
- Medium: LLM parsing defaults silently to 5.0/"Good attempt" on malformed responses.

## 15. Repository audit

### 15.1 Functionality that can be salvaged

| Area | Assessment |
|------|-----------|
| Auth core (JWT, bcrypt, `get_current_user`) | Salvage with hardening; reset-password-temp endpoint removed; enforce verification |
| REST interview session model (`InterviewSession`, `SessionQuestion`) | Salvage the data shape; replace question generation + evaluation internals |
| Video STT (Groq Whisper) + TTS (Edge) | Salvage as-is; move config to env + provider interface |
| `code_runner` Judge0 path | Salvage the Judge0 client; local fallback removed; require config for code execution |
| Exam MCQ auto-grading logic | Salvage; move exam state out of memory |
| Progress aggregation queries | Salvage conceptually; supercede by skill profile later |
| Frontend layout, auth store, api client | Salvage; move backend URL to env config |
| Coding editor UI, Mock exam UI, History/Dashboard UI | Salvage as presentational components for V1 |

### 15.2 Functionality that should be rewritten

| Area | Assessment |
|------|-----------|
| `AIService` | Rewrite around provider abstraction + structured outputs + retries; stop parsing `SCORE:` text |
| Question generation (all flavors) | Rewrite as a controlled, validated, persisted pipeline (Phase 2) |
| Evaluation (`evaluate_answer`, `generate_feedback_report`, `review_code`, `grade_exam_answer`) | Rewrite as criteria-based evaluation with deterministic aggregation |
| `ws.py` | Rewrite to async/DB-session-safe design (or drop until V1 if REST flow is sufficient) |
| `video_service._analyze_confidence` | Rewrite/remove; text-derived "confidence" is an unsupported claim in its current form — document as heuristic or remove |
| Frontend `VideoInterviewPage` media handling | Rewrite using supported browser APIs, or gate the feature until validated |
| `exam` in-memory store | Rewrite with DB or Redis persistence |
| Ad-hoc migrations | Replace with alembic |

### 15.3 Functionality that should be deleted

| Item | Why |
|------|-----|
| `POST /auth/reset-password-temp` | Unauthenticated password reset — security critical |
| `resumeAPI.analyze` in `frontend/src/services/api.js` | No backend endpoint exists |
| `AIService.analyze_resume` (backend) | Unreachable; and the message construction is malformed for the current API |
| Empty stubs: `middleware/auth_middleware.py`, `middleware/rate_limiter.py`, `models/question.py`, `services/feedback_service.py` | Misleading (look active, are empty) |
| `options.js` `case_study`/`domain` interview types | Not valid backend values |
| Unused Vite leftovers: `src/App.css` (unimported), `src/assets/react.svg` | Dead template files |
| Redis config / `REDIS_URL` mention in README as if used | Redis is not used anywhere in the app |
| `add_otp_columns` helper (and README migration step referencing it) | Superseded by the ORM model columns + alembic |

### 15.4 Functionality that should be postponed

- Skill profile / mastery / weakness detection / recommendations → after evaluation + question
  system exist (Phase 2–3 → Phase 5).
- Video interviewing → after written/coding/evaluation foundation (explicit V1 deferral).
- Resume/ATS → `[IDEA]`, not in roadmap phases.
- Company platform (ProctoAI Hire) → Phase 8.
- Billing, org management, SSO, analytics, i18n, scaling → Phase 9.
- Advanced avatar/lip-sync, emotion detection → `[IDEA]`.

### 15.5 Known bugs / architectural mismatches (current code)

1. `signup` sets `is_verified=True`; the whole email-verification UI/OTP flow (`verify-email`,
   `resend-otp`, `/verify-email` route) is therefore dead in practice and the README overstates it.
2. `/video/upload-recording` stores `recording_url` pointing at `/video/recording/{filename}` but
   **no GET route serves those files** — broken link.
3. Video interview UI relies on non-standard browser APIs (likely non-functional in production).
4. `AIService._chat` uses `max_tokens=1000` while `generate_coding_problem` uses 2000 and exam
   generation 4000 — inconsistent and undocumented.
5. Sessions max at 5 questions enforced separately in REST, WS, and video flows (duplicated
   logic) — drift risk.
6. `exam.py` keeps exam state in a process-local dict; lost on restart; breaks with >1 worker.
7. `InterviewPage` may generate an unused 5th question (off-by-one end condition).
8. The "overall score" in interview reports is a separate LLM number, not an aggregation of
   per-question scores — inconsistent definitions between `overall_score` (LLM) and
   `average_score` (computed) returned together.
9. Role strings are free text in the DB but narrow lists in the frontend — a user who sets an
   arbitrary role may get generic or incoherent AI behavior.
10. `code_runner` silently runs local Python subprocesses without sandboxing or resource limits
    when no Judge0 key is configured.
11. `video.py` `session.recording_url = ... if hasattr(session, 'recording_url')` — redundant
    (`recording_url` always exists on the model).
12. `AIService` imports `AIOrchestrator` (new WIP) but the orchestrator is not consulted by any
    actual LLM call — the app still hardcodes Groq.

## 16. Misleading documentation (current)

- `backend/README.md` claims the AI service is "designed to be swappable — only `__init__` and
  `_chat` need to change." True in the narrowest sense, but the service also performs text
  parsing and JSON parsing in ~8 methods; the new orchestrator WIP implies more. The README also
  describes email verification as a completed feature when signup bypasses it.
- `backend/README.md` lists "Redis" as part of the stack and a `Resend email (OTP)` flow; Redis is
  unused and OTP is bypassed by signup.
- Frontend `api.js` dead `resumeAPI` suggests a resume feature that does not exist.

## 17. Interfaces between frontend and backend (current contracts)

- Token exchange: `{access_token, refresh_token, token_type, user}`.
- Interview: `POST /interview/start` → `{session_id, question:{id, question_text, order_index}}`;
  `POST /interview/answer` → `{feedback:{question_id,score,feedback,follow_up}, next_question, session_complete, questions_answered}`.
- Video: `POST /video/start` → `{session_id, question:{id,text,…audio_url}, avatar:{…}}`;
  `POST /video/transcribe` (multipart) → `VideoAnswerFeedback`; `POST /video/end?session_id=…`.
- Coding: `POST /coding/submit` → `SubmissionResponse`.
- Exam: `POST /exam/start` → `ExamStartResponse`; `POST /exam/submit` → `ExamResult`.
- These contracts are changing as the system is reworked — treat this list as current-but-not-stable.

## 18. Data privacy notes (current)

- All student data in the candidate's own DB rows keyed by `user_id`; endpoints filter by
  `user_id` (no cross-user access observed).
- Recordings/audio are stored on local disk and never served back; still a privacy consideration.
- Prompts sent to Groq include the user's answers and role/name-derived context.

## 19. Open architectural decisions (need human discussion)

1. **Provider strategy:** target says OpenRouter primary + Groq for speech. Current reality is
   Groq-everywhere. Confirm the switch and define the adapter interface (HTTP vs vendor SDK).
2. **Question store scope in V1:** do we seed a curated bank + generate-on-demand (validated,
   deduped), or fully generate-then-persist? Affects Phase 2 size.
3. **Evaluation design:** which criteria set for V1? How are weights chosen, and how is the LLM's
   role limited so a single call can't override the aggregate? Replay/versioning format?
4. **Code execution:** self-hosted sandbox (Docker/isolate) vs a managed sandbox API (Judge0 with
   pricing) vs open-source sidecar. Local-subprocess fallback must be removed either way.
5. **Video sequencing:** keep prototype sub-features (TTS/STT) behind a flag during V1, or gate the
   whole page? Confirm "defer video" decision with the owner.
6. **Auth hardening scope:** add refresh-token rotation + revocation in V1 or defer? Enforce email
   verification (flip signup) or drop OTP? Remove temp endpoint immediately regardless.
7. **Frontend config:** introduce `VITE_API_URL` and stop hardcoding production; add a dev proxy.
8. **Monorepo tooling:** single repo is fine; decide on lint/test/CI baseline for V1 (backend
   ruff+pytest, frontend eslint+vitest) and a migration strategy (alembic) before implementing.
9. **Schema versioning for AI contracts:** define a structured-output contract (Pydantic) for every
   LLM call, with a `prompt_version` and `model` recorded on artifacts.
10. **Session/question persistence for in-flight LLM state:** ensure WebSocket/REST flows share one
    implementation rather than duplicated 5-question logic.

## 20. Recommendation (high-level)

Do not "start coding everything". Sequence: remove the temp password-reset endpoint and the local
code-execution fallback **now** (security); decide the open decisions above; then implement in
Phase order (hardening → question system → evaluation → coding → profile → polish). Details in
[PRODUCT_ROADMAP](PRODUCT_ROADMAP.md).