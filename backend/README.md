# ProctoAI — Backend

AI-powered interview coaching and assessment platform backend built with FastAPI and PostgreSQL.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11) |
| Database | PostgreSQL + SQLAlchemy (sync) |
| Auth | JWT (access + refresh tokens) + bcrypt |
| AI | Groq (LLaMA 3.3 70B) |
| TTS | Microsoft Edge TTS |
| STT | Groq Whisper |
| Email | Resend |
| Cache | Redis |
| Server | Uvicorn |
| Deployment | Render |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, middleware, startup
│   ├── core/
│   │   ├── config.py            # Environment variables (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine, session, migrations
│   │   └── security.py          # JWT, bcrypt, auth dependencies
│   ├── models/
│   │   ├── users.py             # User model
│   │   ├── session.py           # InterviewSession, SessionQuestion
│   │   └── submission.py        # CodingProblem, CodeSubmission
│   ├── schemas/
│   │   ├── auth.py              # Signup, login, token schemas
│   │   ├── interview.py         # Session, question, feedback schemas
│   │   ├── coding.py            # Problem, submission schemas
│   │   ├── video.py             # Video session schemas
│   │   └── exam.py              # Mock exam schemas
│   ├── routers/
│   │   ├── auth.py              # Auth endpoints
│   │   ├── interview.py         # Interview session endpoints
│   │   ├── coding.py            # Coding challenge endpoints
│   │   ├── video.py             # Video interview endpoints
│   │   ├── exam.py              # Mock exam endpoints
│   │   ├── progress.py          # Dashboard & history endpoints
│   │   └── ws.py                # WebSocket endpoint
│   └── services/
│       ├── ai_service.py        # All Groq AI calls
│       ├── email_service.py     # Resend email (OTP)
│       ├── tts_service.py       # Edge TTS (text to speech)
│       ├── stt_service.py       # Groq Whisper (speech to text)
│       ├── video_service.py     # Video processing
│       └── code_runner.py       # Code execution sandbox
├── docker-compose.yml           # Local PostgreSQL + Redis
├── requirements.txt
├── Procfile                     # Render start command
└── runtime.txt                  # Python version pin
```

---

## API Routes

### Auth — `/auth`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout (stateless) |
| GET | `/auth/me` | Get current user profile |
| PATCH | `/auth/me` | Update profile (name, role, level) |
| POST | `/auth/change-password` | Change password |
| POST | `/auth/verify-email` | Verify email with OTP |
| POST | `/auth/resend-otp` | Resend OTP to email |

### Interview — `/interview`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interview/start` | Start new interview session |
| POST | `/interview/answer` | Submit answer, get AI feedback |
| POST | `/interview/end` | End session, get full report |
| GET | `/interview/sessions` | Get all user sessions |
| GET | `/interview/session/{id}` | Get session with Q&A detail |

### Video Interview — `/video`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/video/start` | Start video interview session |
| POST | `/video/transcribe` | Transcribe audio answer |
| POST | `/video/upload-recording` | Upload session recording |
| POST | `/video/end` | End video session |
| GET | `/video/question/{id}/audio` | Get TTS audio for question |

### Coding — `/coding`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/coding/problems` | List coding problems |
| POST | `/coding/generate` | AI-generate a coding problem |
| POST | `/coding/run` | Run code (sandbox) |
| POST | `/coding/submit` | Submit solution for AI review |
| GET | `/coding/submissions` | Get user submissions |

### Mock Exam — `/exam`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/exam/start` | Generate exam questions |
| POST | `/exam/submit` | Submit exam, get graded results |

### Progress — `/progress`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/progress/dashboard` | Dashboard stats and charts data |
| GET | `/progress/history` | Full session history |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@127.0.0.1:5432/interviewai

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
GROQ_API_KEY=your-groq-api-key
AI_MODEL=llama-3.3-70b-versatile

# Email
RESEND_API_KEY=your-resend-api-key

# App
APP_NAME=ProctoAI
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Docker Desktop
- Git

### 1. Clone the repo
```bash
git clone https://github.com/VivekGarari/ai-interview.git
cd ai-interview/backend
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL and Redis
```bash
docker-compose up -d
```

### 5. Set up environment variables
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 6. Run database migrations
```bash
python -c "from app.core.database import add_otp_columns, add_model_answer_column; add_otp_columns(); add_model_answer_column()"
```

### 7. Start the server
```bash
uvicorn app.main:app --reload
```

Server runs at **http://127.0.0.1:8000**
Swagger docs at **http://127.0.0.1:8000/docs**

---

## AI Service

All AI calls go through `app/services/ai_service.py`. The service is designed to be swappable — to switch from Groq to another provider, only `AIService.__init__` and `_chat` need to change.

| Method | Description |
|--------|-------------|
| `generate_question` | Generates interview questions based on role and type |
| `evaluate_answer` | Scores answer 0-10, gives feedback and model answer |
| `generate_feedback_report` | Full session report with strengths and improvements |
| `generate_coding_problem` | Creates coding challenge for a given topic and difficulty |
| `review_code` | Reviews code solution for correctness and quality |
| `generate_exam_questions` | Generates mixed MCQ/short answer/coding exam |
| `grade_exam_answer` | AI grades short answer and coding exam questions |
| `generate_exam_summary` | Summarizes exam performance with recommendations |

---

## Database Models

### User
- `id`, `email`, `hashed_password`, `full_name`
- `target_role`, `experience_level` (plain strings, 30+ roles supported)
- `is_active`, `is_verified`
- `otp_code`, `otp_expires_at` (for email verification)

### InterviewSession
- Linked to `User`
- Stores `interview_type`, `target_role`, `difficulty`, `status`
- Final results: `overall_score`, `ai_summary`, `strengths`, `improvements`

### SessionQuestion
- Linked to `InterviewSession`
- Stores `question_text`, `answer_text`, `score`, `ai_feedback`, `model_answer`

### CodingProblem / CodeSubmission
- AI-generated problems with examples, constraints, hints
- Submissions store code, output, AI review, quality score

---

## Deployment (Render)

1. Push code to GitHub
2. Create a new **Web Service** on Render
3. Set **Root Directory** to `backend`
4. Set **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables in the **Environment** tab
6. Add a **PostgreSQL** database and copy the `DATABASE_URL` to environment variables

Live backend: **https://proctoai-backend.onrender.com**

---

## Notes

- Uses **sync psycopg2** (not asyncpg) for Python 3.11+ compatibility
- All router functions are **synchronous** (no async/await)
- Tables are auto-created on startup via `create_tables()`
- Column migrations run automatically on startup
- Free Render tier spins down after 15 min inactivity — use UptimeRobot to keep alive