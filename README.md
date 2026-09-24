# ProctoAI

> AI-powered interview preparation and interview simulation platform for students and early-career candidates.

This repository contains the **current prototype** of ProctoAI. The documentation in this repository
separates what is **already implemented** from what is **planned**. Read the
[Documentation Map](#documentation-map) before working on any part of the system.

---

## What ProctoAI is

ProctoAI is a long-term product idea: a platform that helps candidates close the gap between
**what they know** and **how well they perform in an interview**. It is being built to combine
learning, concept understanding, written + video interview simulation, coding practice, and
structured, explainable feedback.

It is **not** just an AI question generator. The differentiator is connecting these experiences:

```
Student
  → Knowledge / Skill Profile
    → Learning + Practice
      → Concept Understanding
        → Written Interview → Coding Practice → Video Interview
          → Structured Evaluation
            → Weakness Detection
              → Personalized Recommendations
                → Improvement
```

## Who it is for

- **Primary (V1):** students and early-career candidates preparing for technical interviews.
- **Future business product:** companies/startups hosting technical assessments (see
  [Company Platform](docs/COMPANY_PLATFORM.md) — *future*, not built).

The product will launch initially in India at small scale for validation, but is designed with an
international/global audience in mind.

## Core problem

Candidates often understand technical concepts and even know the answers, yet perform poorly in
interviews because of inexperience, anxiety, poor communication, weak problem-solving practice,
shallow conceptual depth, or unfamiliarity with interview pressure.

ProctoAI's goal is to help a student: learn concepts, understand them deeply, identify
conceptual gaps, practice explaining ideas, experience realistic interview pressure, practice
coding, receive structured feedback, understand strengths/weaknesses, improve over time, and
become more confident in technical interviews.

## Current development status

**This is an early, working prototype ("pre-V1"), not the finished product.**

| Aspect | Current status |
|--------|----------------|
| Backend | FastAPI (Python 3.11), SQLAlchemy sync + PostgreSQL, JWT auth, deployed on Render |
| Frontend | React 19 + Vite + Tailwind, deployed as a static site |
| AI today | **Groq** (LLaMA 3.3 70B) for LLM tasks, **Groq Whisper** for speech-to-text, **Edge TTS** for interviewer voice |
| Written interview | Implemented (text chat, AI questions/feedback, session reports) |
| Video interview | Partially implemented (audio recording → STT → text analysis); see [Video Interview](docs/VIDEO_INTERVIEW.md) |
| Coding | Partially implemented (AI problem generation, code run, AI review); no real test-case grading |
| Mock exam | Implemented, but exam state is held in server memory only |
| Skill profile / mastery / recommendations | **Not implemented** (dashboard is aggregate stats only) |
| Company/business platform (ProctoAI Hire) | **Not implemented / future** |
| Question store, taxonomy, question versioning | **Not implemented** (AI generates fresh each session) |
| Structured AI outputs / provider abstraction | **Partially scaffolded, not productionized** |

Precise, file-by-file audit of what exists: [Repository Audit](docs/ARCHITECTURE.md#15-repository-audit).
Anything marked `[FUTURE]` or `[IDEA]` in the docs is **not** present today and should never be
described as existing.

## V1 scope (recommended)

V1 is scoped as **ProctoAI Interview Lab**: role/domain + language + topic/skill + difficulty,
then a concept practice → AI written interview → follow-ups → structured evaluation → coding
challenge → coding evaluation → personalized report flow. Video interviewing is deferred out of
V1 until the written/coding/evaluation foundation is reliable.

See [V1 Scope](docs/V1_SCOPE.md) for the full in/out-of-scope list.

## Long-term vision

Long-term the product splits conceptually into:

- **ProctoAI Learn** — students/candidates: learning, preparation, interview simulation, personal progress.
- **ProctoAI Hire** — companies/recruiters: assessments, candidate evaluation, hiring workflows.

Both share core assessment/evaluation infrastructure but keep clearly separated product
boundaries, permissions, workflows and data access. See [Product Vision](docs/PRODUCT_VISION.md)
and [Roadmap](docs/PRODUCT_ROADMAP.md).

## High-level architecture (target)

```
Student app (React)  ──HTTP/WS──▶  ProctoAI API (FastAPI)
                                     ├── Auth / users
                                     ├── Question system (taxonomy → generation → validation → persistence)
                                     ├── Interview engine (written/video/coding sessions)
                                     ├── Evaluation engine (deterministic aggregation, LLM-assisted rubric scoring)
                                     ├── Skill profile (mastery, weakness detection, recommendations)
                                     └── LLM Interface (provider abstraction)
                                          ├── OpenRouter (target primary general LLM)
                                          ├── Groq (target: speech/specialized)
                                          └── future providers
```

Current implementation is a simplified version of this (single LLM provider, no question store,
no skill profile). See [Architecture](docs/ARCHITECTURE.md) for current vs target.

## Repository structure

```
/
├── backend/                  # FastAPI application (Python 3.11)
│   ├── app/
│   │   ├── core/             # config, database engine, security/JWT
│   │   ├── models/           # SQLAlchemy models (users, sessions, submissions)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # auth, interview, video, coding, exam, progress, ws, ai
│   │   └── services/         # ai_service, code_runner, stt/tts/video, email
│   ├── tests/                # unit tests (currently minimal)
│   ├── docker-compose.yml    # local PostgreSQL + Redis
│   └── README.md             # backend-specific README (legacy notes)
├── frontend/                 # React 19 + Vite + Tailwind SPA
│   └── src/
│       ├── pages/            # Login, Dashboard, Interview, Video, Coding, Exam, History, Settings
│       ├── components/       # Layout
│       ├── services/         # API client
│       └── store/            # zustand auth store
└── docs/                     # <-- all product/architecture documentation lives here
```

## Development setup

Quick start (details in [Development](docs/DEVELOPMENT.md)):

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d                              # PostgreSQL + Redis (local)
cp .env.example .env                              # fill in DATABASE_URL + API keys
uvicorn app.main:app --reload                     # http://127.0.0.1:8000/docs

# Frontend
cd frontend
npm install
npm run dev                                       # http://localhost:5173
```

> Note: `frontend/src/services/api.js` hardcodes the production backend URL
> (`https://proctoai-backend.onrender.com`). For local development you must edit it or the app
> will talk to production.

## Documentation Map

| Document | Contents |
|----------|----------|
| [Product Vision](docs/PRODUCT_VISION.md) | What ProctoAI is intended to become; the full experience; major product areas |
| [V1 Scope](docs/V1_SCOPE.md) | Recommended near-term build (ProctoAI Interview Lab) and explicit out-of-scope list |
| [Product Roadmap](docs/PRODUCT_ROADMAP.md) | Staged plan (Phase 0–9), with current-state mapping |
| [Architecture](docs/ARCHITECTURE.md) | Current vs target architecture, component breakdown, repository audit, mismatches, dead code |
| [AI System](docs/AI_SYSTEM.md) | LLM provider abstraction, OpenRouter/Groq intent, structured outputs, "LLM is not source of truth" |
| [Question System](docs/QUESTION_SYSTEM.md) | Intended taxonomy, question blueprint, generation/validation/dedup/persistence pipeline |
| [Evaluation System](docs/EVALUATION_SYSTEM.md) | Structured multi-dimension evaluation model and deterministic aggregation |
| [Interview System](docs/INTERVIEW_SYSTEM.md) | Written AI interview flow (current + target adaptive probing) |
| [Coding System](docs/CODING_SYSTEM.md) | Coding practice environment (current + target secure execution & grading) |
| [Video Interview](docs/VIDEO_INTERVIEW.md) | Audio/video interview (current TTS/STT pipeline + target communication analysis) |
| [Company Platform](docs/COMPANY_PLATFORM.md) | ProctoAI Hire — future B2B assessments product (not built) |
| [Data Model](docs/DATA_MODEL.md) | Current tables + planned conceptual entities, clearly separated |
| [Security](docs/SECURITY.md) | Security requirements, current findings/risk register |
| [Development](docs/DEVELOPMENT.md) | Setup, run, test, deploy, conventions |

## Documentation rules used in this repository

- Status labels are used consistently across docs: `[IMPLEMENTED]`, `[PARTIAL]`, `[V1]`,
  `[FUTURE]`, `[IDEA]`. See the legend in [Architecture](docs/ARCHITECTURE.md#status-legend).
- Planned features are **never** described as if they exist.
- No fake API endpoints or fake database tables are documented as real.
- When implementation begins later, documentation must be updated in the same change.