# ProctoAI Implementation Plan

This is the authoritative execution plan for the current ProctoAI development checkpoints. It records what is complete, what is partial or open, what is deliberately deferred, and the dependency-aware order for future work.

This plan describes the current repository as it exists. Future architecture is not treated as implemented until code, tests, verification, and documentation are complete.

## Working Method

Each checkpoint follows this sequence:

1. Define the objective and contract.
2. Perform a read-only audit where appropriate.
3. Make the smallest scoped implementation.
4. Add focused tests.
5. Run the full regression suite.
6. Update relevant documentation.
7. Verify the Git diff and working tree.
8. Record an explicit definition of done.

Security findings must not be forgotten. Every OPEN security issue has a designated future checkpoint.

## COMPLETED CHECKPOINTS

### Checkpoint 1 — Repository / Architecture Assessment

**Status: COMPLETE**

The existing implementation was audited before major rebuilding. The audit established that the old implementation was prototype-level and had important architectural and security weaknesses:

- The AI layer was tightly coupled to Groq.
- Question generation was mostly live, free-text AI generation.
- No proper persistent generated-question model existed.
- Code execution had an unsafe local subprocess fallback.
- Database startup performed schema mutation.
- Authentication and security had weaknesses.
- Frontend/API integration had issues.
- Documentation was inaccurate in places.

The project direction moved toward a modular, controlled architecture.

### Checkpoint 2 — Documentation / Product Architecture Foundation

**Status: COMPLETE**

The existing documentation set defines product direction, V1 scope, architecture, AI, questions, evaluation, interviews, coding, video, company platform, data, and security. The primary references are:

- [Product Vision](PRODUCT_VISION.md)
- [V1 Scope](V1_SCOPE.md)
- [Product Roadmap](PRODUCT_ROADMAP.md)
- [Architecture](ARCHITECTURE.md)
- [AI System](AI_SYSTEM.md)
- [Question System](QUESTION_SYSTEM.md)
- [Evaluation System](EVALUATION_SYSTEM.md)
- [Interview System](INTERVIEW_SYSTEM.md)
- [Coding System](CODING_SYSTEM.md)
- [Video Interview](VIDEO_INTERVIEW.md)
- [Company Platform](COMPANY_PLATFORM.md)
- [Security](SECURITY.md)

### Checkpoint 3 — Security Phase 1

**Status: COMPLETE**

- Removed unauthenticated `POST /auth/reset-password-temp`.
- Removed `_run_local()` and local `subprocess.run` code execution.
- Missing Judge0 configuration now fails safely.
- Added and strengthened security regression tests.

### Checkpoint 4 — Question System Foundation

**Status: COMPLETE**

Created the persistent taxonomy and question model foundation:

```text
Domain
  ↓
Topic
  ↓
Subtopic
  ↓
Question
  ↓
QuestionVersion
```

The `Question` model does not directly contain `topic_id`. `QuestionService` currently supports question creation, topic filtering, random selection, enum validation, subtopic validation, and QuestionVersion creation. Focused tests were added and pass.

### Checkpoint 5 — Interview / Question Integration

**Status: PARTIAL**

Persistent Question content can be consumed when a matching topic is explicitly supplied through the private selection helper. The normal public `start_session()` path currently passes `topic_id=None`, so normal interview startup still falls back to AI-generated text.

Full interview/question integration is not complete.

### Checkpoint 6 — Environment-Driven Configuration

**Status: COMPLETE**

Centralized settings cover application, database, Redis, authentication, AI providers, Judge0, email, storage, TTS, and STT configuration. `.env.example` contains placeholders only and the actual `.env` is not committed.

### Checkpoint 7 — AI Provider Abstraction / OpenRouter

**Status: COMPLETE**

Implemented and verified:

- `AIProvider` protocol
- `OpenRouterProvider`
- `GroqProvider`
- provider factory
- environment-driven provider selection
- timeout and retry handling
- normalized chat-completion responses
- AIService routing through the provider abstraction

OpenRouter was successfully tested with a real request. Current provider selection remains environment-driven.

### Checkpoint 8 — Error / Configuration Audit

**Status: COMPLETE**

Fixed and verified:

- Judge0 settings consumed by `CodeRunner`.
- Frontend lint errors.
- Frontend build validation issues.

Verification completed with backend tests, focused security tests, frontend lint, frontend build, Python compilation, and `git diff --check`.

### Checkpoint 9 — Infrastructure Health Audit

**Status: COMPLETE**

Verified backend dependencies, PostgreSQL connectivity, Question System tables, OpenRouter configuration, frontend lint/build, Compose syntax, CORS configuration, and Judge0 safe-failure behavior.

Redis is configured but is not required by active Question Generation paths.

Deferred configuration findings:

- STT still hard-codes provider URL/model values instead of fully consuming centralized settings.
- `CODE_RUNNER_PROVIDER` is declared but does not currently select an implementation.

### Checkpoint 10 — Database Audit

**Status: COMPLETE**

Verified PostgreSQL connectivity, SQLAlchemy/model alignment, all expected tables, Question System foreign keys, indexes, constraints, enums, timestamp types, referential integrity, and duplicate baselines. Current Question System tables are empty.

Known architectural issue: startup still performs `create_all()` and raw `ALTER TABLE` operations. No controlled Alembic workflow has been established.

### Checkpoint 11 — Security / Backdoor / Open-Door Audit

**Status: COMPLETE**

Read-only audit result: no confirmed backdoor was found.

No confirmed hidden admin account, hard-coded privileged account, magic authentication token, temporary password-reset backdoor, local shell execution backdoor, tracked real credentials, tracked `.env`, or tracked source maps/build output was found.

The real security findings remain open in the remediation register below.

## Security Remediation Plan

Security findings must not be dropped because they do not affect the current feature. Each open finding has a designated checkpoint, status, blocking classification, and test requirement.

| ID | Severity | Finding | Current status | Planned checkpoint | Question Generation blocker | Production blocker | Required verification |
|---|---|---|---|---|---|---|---|
| SEC-001 | HIGH | Exam submission BOLA/IDOR: exam ownership is not checked before grading/deletion | OPEN | Phase A — Access Control | NO | YES | User B cannot submit User A's exam; owner can submit own exam |
| SEC-002 | HIGH | Video question audio is public and has no session ownership check | OPEN | Phase A — Access Control | NO | YES | Anonymous access rejected; cross-user access rejected; owner access succeeds |
| SEC-003 | HIGH | Signup marks accounts verified and issues tokens immediately | OPEN | Phase A — Authentication | NO | YES if verification is required | New user starts unverified; valid OTP verifies; invalid OTP does not |
| SEC-004 | HIGH | No effective rate limiting or abuse controls for auth, AI, coding, uploads, or processing | OPEN | Phase G — Security Hardening | NO for local development | YES | Endpoint-specific throttling and quota tests |
| SEC-005 | HIGH | Access and refresh JWTs are stored in browser `localStorage` | OPEN | Phase G — Session / Token Security | NO | YES for hardened production | Token storage, rotation, revocation, and logout tests |
| SEC-006 | MEDIUM | Audio/video uploads have insufficient size, type, duration, and storage controls | OPEN | Phase I — Video Interview | NO | YES for video production | Oversize, invalid-type, duration, and quota tests |
| SEC-007 | MEDIUM | WebSocket authentication does not consistently enforce `is_active` | OPEN | Phase I — WebSocket Hardening | NO | YES for WebSocket production | Inactive-user and session-state tests |
| SEC-008 | MEDIUM | Raw exception information may reach clients or logs | OPEN | Phase G — Production Hardening | NO | YES | Sanitized client errors and safe logging tests |
| SEC-009 | MEDIUM | OTP/account flows permit enumeration and lack strong attempt controls | OPEN | Phase G — Authentication / OTP | NO | YES | Uniform responses, secure OTP, attempt, and resend-limit tests |
| SEC-010 | MEDIUM | Application startup performs `create_all()` and raw `ALTER TABLE` schema mutation | OPEN | Phase H — Database / Migration Hardening | NO | YES for controlled schema management | Migration-only deployment and startup read-only tests |

When a remediation checkpoint is completed, update the finding status, tests, verification evidence, and [Security](SECURITY.md) where relevant.

## Chronological Development Roadmap

### Phase A — Immediate Security Remediation

**Next implementation checkpoint.**

Objective: fix the three access-control/authentication findings that directly expose user data or bypass intended verification.

1. Fix exam ownership validation.
2. Fix video question-audio authentication and ownership.
3. Fix email verification behavior and verified-user enforcement.
4. Add focused regression tests.
5. Run the full backend regression suite and frontend validation.
6. Update security documentation.
7. Verify Git status and diff.

Definition of done: the three access-control flows reject unauthorized requests, legitimate owner flows still work, tests pass, and the security register is updated.

### Phase B — Question Generation Foundation

**Status: NOT STARTED**

Objective: build a production-grade, controlled generation pipeline.

```text
Taxonomy
    ↓
Question Requirements
    ↓
Question Generator
    ↓
Structured LLM Output
    ↓
Schema Validation
    ↓
Semantic Validation
    ↓
Deduplication
    ↓
QuestionVersion
    ↓
Question Persistence
    ↓
Question Selection
```

Target services:

- `QuestionGenerator`
- `QuestionValidator`
- `QuestionDeduplicator`
- `QuestionService` integration

First checkpoint: read-only audit plus a Question Generation Contract defining inputs, taxonomy context, difficulty, question type, competencies, model output, validation, semantic requirements, duplicate detection, versioning, persistence, and failure behavior.

Required tests:

- Valid generation
- Malformed model output
- Schema validation
- Semantic validation
- Deduplication
- Persistence
- Integration

Update [Question System](QUESTION_SYSTEM.md), [AI System](AI_SYSTEM.md), and relevant architecture documentation in the same change.

### Phase C — Interview Question Integration

**Status: NOT STARTED**

Complete the current partial integration:

- Expose appropriate domain/topic selection at interview start.
- Connect persistent Question selection to normal interview startup.
- Preserve Question/QuestionVersion identity where appropriate.
- Avoid unnecessary duplication of source-of-truth question data.
- Define historical snapshot behavior.
- Add integration tests.

### Phase D — Structured Evaluation System

**Status: NOT STARTED**

Build:

```text
Answer
    ↓
Evaluation Rubric
    ↓
Structured Evaluation
    ↓
Dimension Scores
    ↓
Evidence
    ↓
Feedback
    ↓
Follow-up Decision
```

Eventually support technical knowledge, conceptual depth, reasoning, communication, coding, and interview performance. Evaluation output must be schema-validated and aggregation must be deterministic.

Reference: [Evaluation System](EVALUATION_SYSTEM.md).

### Phase E — Adaptive Follow-Up System

**Status: NOT STARTED**

Implement question selection based on answer evaluation, weakness/gap identification, deeper follow-up selection, and final evaluation. Document state transitions and decision rules before implementation.

### Phase F — Coding System Hardening

**Status: NOT STARTED**

Build and harden:

```text
Problem
    ↓
Code
    ↓
Judge0
    ↓
Test Cases
    ↓
Correctness
    ↓
Complexity
    ↓
Code Quality
    ↓
Explanation
    ↓
Integrated Evaluation
```

Address execution-provider architecture, request-size limits, Judge0 abuse controls, and secure result handling. The current safe no-local-execution behavior must remain intact.

Reference: [Coding System](CODING_SYSTEM.md).

### Phase G — Security Hardening

**Status: NOT STARTED**

Address the remaining authentication, rate-limiting, session/token, OTP, error-leakage, security-header, HTTPS/host-policy, CORS-policy, API-exposure, and AI-spend-control work recorded in the security register.

Run a second repository-wide security audit after remediation.

### Phase H — Database / Migration Hardening

**Status: NOT STARTED**

Replace startup schema mutation with a controlled migration workflow. Establish Alembic configuration, migration conventions, migration testing, deployment procedure, and rollback guidance where practical.

Do not silently introduce migrations during unrelated feature work.

### Phase I — Video Interview

**Status: DEFERRED**

Begin only after written interview, evaluation, coding, and core data foundations are reliable.

Implement secure audio/video handling, STT, upload controls, video analysis, structured communication analysis, technical correctness, answer structure, pacing/filler analysis, and appropriate limitations on psychological inference.

### Phase J — Student Profile / Mastery

**Status: NOT STARTED**

Build skill profile, concept mastery, weakness detection, progress tracking, personalized recommendations, and historical evaluation aggregation.

### Phase K — Production Infrastructure

**Status: NOT STARTED**

Before public launch, establish production secrets management, migrations, Redis where needed, storage, rate limits, monitoring, logging, security headers, HTTPS, CORS policy, backups, database protection, dependency/security scanning, deployment hardening, and API documentation policy.

### Phase L — ProctoAI Hire

**Status: DEFERRED**

Define the separate B2B boundary for companies, recruiters, assessments, candidates, organization membership, permissions, tenant isolation, company data access, and billing. Reuse shared infrastructure only where boundaries are explicit.

Reference: [Company Platform](COMPANY_PLATFORM.md).

## Deferred Items

The following are deliberately out of the current checkpoint:

- Video redesign
- Adaptive interview before evaluation foundations
- Billing
- Company platform
- ProctoAI Hire
- Redis integration unless required by an active feature
- Analytics
- Recommendation engine
- Production deployment
- Frontend redesign
- Large-scale optimization
- Unnecessary database indexes
- Security hardening unrelated to the current checkpoint

## Current Status

| Checkpoint | Status | Notes | Blocking next step? |
|---|---|---|---|
| Architecture assessment | COMPLETE | Prototype and architectural risks documented | No |
| Product/documentation foundation | COMPLETE | Product, scope, architecture, and system docs exist | No |
| Security Phase 1 | COMPLETE | Reset bypass and local execution removed | No |
| Question System foundation | COMPLETE | Taxonomy, questions, versions, service, and tests exist | No |
| Interview question integration | PARTIAL | Normal startup does not yet pass topic context | Yes for persistent interview selection |
| Environment configuration | COMPLETE | Centralized settings and safe template exist | No |
| AI provider abstraction | COMPLETE | OpenRouter/Groq factory and normalized provider path | No |
| OpenRouter integration | VERIFIED | Real request previously succeeded | No |
| Error audit | COMPLETE | Configuration and frontend validation issues fixed | No |
| Infrastructure audit | COMPLETE | Dependencies, DB, providers, Compose, CORS, and safe failure reviewed | No |
| Database audit | COMPLETE | Schema and integrity baseline verified | No |
| Backdoor/security audit | COMPLETE | No confirmed backdoor; open findings registered | Phase A |
| SEC-001 | OPEN | Exam ownership | Phase A |
| SEC-002 | OPEN | Video audio authorization | Phase A |
| SEC-003 | OPEN | Email verification | Phase A |
| Question Generation | NOT STARTED | Requires contract checkpoint first | Yes |
| Evaluation system | NOT STARTED | Structured rubric/evaluation not implemented | No |
| Adaptive follow-up | NOT STARTED | Depends on evaluation | No |
| Coding hardening | NOT STARTED | Judge0-only foundation exists; grading hardening remains | No |
| Video | DEFERRED | Waits for written/coding/evaluation reliability | No |
| Production hardening | NOT STARTED | Security, migrations, monitoring, deployment controls remain | No |
| ProctoAI Hire | DEFERRED | Separate future B2B product boundary | No |

## Definition of Current Done

The current checkpoint is complete when:

- The documentation accurately distinguishes complete, partial, open, deferred, and not-started work.
- All ten open security findings are tracked and assigned to future checkpoints.
- Question Generation remains marked NOT STARTED.
- Phase A security remediation is explicitly the next implementation checkpoint.
- No source code, tests, configuration, or database schema is changed by this documentation update.
