# AI System — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Describes how ProctoAI talks to LLMs: the **target provider abstraction**, the provider
intent (OpenRouter / Groq), the non-negotiable rule that *the LLM is not the source of truth*,
and the **current** implementation reality.

## 2. The core rule

> **The LLM must not be the source of truth.**

Every AI-assisted artifact must pass through validation before it is persisted or used:

- LLM output → schema validation → semantic validation → deduplication (where relevant) →
  persistence.

Scores and evaluations must be aggregated deterministically on the application side wherever
possible, and must remain reproducible (stored question + rubric + answer + prompt/model version).

## 3. Target: provider abstraction

```
Application
   ↓
LLM Interface   (retries, timeouts, structured outputs, prompt versioning, model config)
   ↓
Provider Adapter
   ├── OpenRouter ───────── (intended primary general-purpose LLM provider)
   ├── Groq ─────────────── (speech-related workloads / alternate provider)
   └── future providers
```

Design guidance:

- Provide **one** adapter contract (chat/complete + structured output). Do not expose provider
  specifics to the rest of the app.
- **OpenRouter** is currently intended to be the primary general-purpose LLM provider.
- **Groq** may remain useful for specific workloads such as speech services (e.g. Whisper
  transcription today) or as an alternate provider.
- **Do not build a complicated dynamic capability-routing system unless there is a real
  requirement.** The current WIP `orchestrator.py` / `/ai/route` is exactly that kind of
  machinery — it must be justified by a real need before it becomes production logic.

Required system behaviors (`[V1]`):

- structured outputs
- JSON schema validation
- retries
- timeouts
- prompt versioning
- model configuration
- provider configuration
- deterministic application-side logic where possible

## 4. Current implementation reality

### 4.1 LLM calls — `backend/app/services/ai_service.py`, `providers.py` `[PARTIAL]`

- `AIService` keeps the existing public methods and prompt/response behavior.
- `app/services/providers.py` contains the small provider interface, HTTP implementation,
  OpenRouter adapter, Groq adapter, and configuration-driven factory.
- The factory selects `DEFAULT_PROVIDER` only when that provider is included in
  `ENABLED_PROVIDERS`. Currently supported LLM providers are `openrouter` and `groq`.
- OpenRouter uses `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, and `OPENROUTER_MODEL`.
- Groq uses `GROQ_API_KEY`, `GROQ_BASE_URL`, and `GROQ_LLM_MODEL`.
- Requests use `AI_REQUEST_TIMEOUT_SECONDS` and retry transient failures up to
  `AI_MAX_RETRIES` times.
- Missing credentials, disabled/unsupported providers, timeouts, HTTP failures, and invalid
  provider responses produce controlled provider errors. API keys and authorization headers are
  not included in error messages.
- Methods: `generate_question`, `evaluate_answer`, `generate_feedback_report`,
  `generate_coding_problem`, `review_code`, `generate_exam_questions`, `grade_exam_answer`,
  `generate_exam_summary`, and dead `analyze_resume`.
- Output handling is **not** structured:
  - `evaluate_answer` / `generate_feedback_report`: prompt asks for a `LABEL: value` text format
    and the response is parsed line-by-line with `startswith("SCORE:")` etc. On any parse failure
    the code silently returns `score=5.0` / `"Good attempt."`.
  - coding/exam/summary methods request JSON and fall back to a hardcoded default object when
    parsing fails.
- Prompt versioning and model/prompt metadata persistence are still not implemented.

Developer configuration is supplied through `backend/.env` locally, using
`backend/.env.example` as the safe template. For OpenRouter, configure
`DEFAULT_PROVIDER=openrouter`, include `openrouter` in `ENABLED_PROVIDERS`, and set the three
OpenRouter variables above. Groq remains available by configuring the equivalent Groq variables.

### 4.2 Provider "routing" WIP — `orchestrator.py`, `routers/ai.py` `[PARTIAL]`

- A dataclass-based `ProviderConfig` / `AIOrchestrator` with legacy `select_provider(task_type,
  capabilities)` heuristics and a `get_capabilities` list.
- Exposed via `GET /ai/capabilities` and `POST /ai/route`.
- **Important:** actual LLM calls do not use these task heuristics. `AIService` uses the provider
  factory and the configured default/enabled providers. The route remains a compatibility WIP and
  is not the provider execution path.

### 4.3 Speech services `[IMPLEMENTED]`

- STT: Groq Whisper (`app/services/stt_services.py`) — direct HTTP call to the Groq audio
  transcriptions endpoint.
- TTS: Edge TTS (`app/services/tts_service.py`) — free, keyless.

## 5. Target: question generation pipeline

```
Taxonomy
  → Question requirements
    → LLM generation
      → Schema validation
        → Semantic validation
          → Deduplication
            → Persistence
              → Question becomes usable
```

See [Question System](QUESTION_SYSTEM.md).

## 6. Target: evaluation pipeline

```
Stored question
  → Expected concepts
    → Evaluation criteria
      → Student answer
        → LLM evaluation (against a known rubric)
          → Structured evaluation
            → Deterministic aggregation
              → Stored result
```

See [Evaluation System](EVALUATION_SYSTEM.md).

## 7. Prompt injection — required posture

User-provided content (answers, resumes, code) is untrusted input. As the system grows:

- Enclose user content in delimited blocks; instruct the model to treat everything inside the
  block as data.
- Never let model output be executed as code, parsed as SQL, or concatenated into config.
- Validate structured outputs with Pydantic schemas before use.
- Keep prompt templates versioned and auditable.
- Record the `prompt_version` + `model` on every stored AI artifact for reproducibility.

This is `[V1]` work; today user answers are interpolated directly into prompt templates with no
delimiting or instruction-resistance hardening.

## 8. Unknowns / open decisions

1. Confirm OpenRouter-as-primary switch (who owns the key, cost ceilings, model choices per task).
2. What Groq keeps (STT today; possibly a fast alternate LLM for high-volume probes).
3. Whether the WIP orchestrator/capability-router is kept (only if a real requirement emerges) or
   deleted in favor of one simple adapter.
4. Structured-output method per provider: provider-native JSON mode vs prompt+parse+Pydantic —
   decide once OpenRouter is wired.


   <!-- session code=opencode -s ses_f50c915e5ffe05Lx6P5m4YWrpn -->