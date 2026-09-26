# Security — ProctoAI

This document describes the current security posture of the ProctoAI repository, with a focus on
remediations completed in Phase 1 and remaining work for future phases.

## Phase 1 Remediations (Current)

### 1. Unauthenticated Password Reset — REMOVED

**Vulnerability**: `POST /auth/reset-password-temp` allowed any caller to reset another user's password
by submitting the target user's email address. No authentication or authorization checks were
performed.

**Remediation**: The endpoint has been **removed entirely** from `backend/app/routers/auth.py`.
- The `reset_password_temp` function and `/reset-password-temp` route are no longer registered.
- Any request to `/auth/reset-password-temp` now returns 404 (route not found).
- No replacement password-reset flow is provided in this phase. A proper flow with
  authenticated ownership checks, email verification tokens, and rate limiting will be
  implemented in a future authentication-hardening phase.

**Current behavior**:
- Unauthenticated password reset: **Not possible** (endpoint removed)
- Legitimate authenticated password change: **Not available** (not implemented in V1);
  users must use the signup flow to create a new account if needed

### 2. Unsafe Local Code Execution — REMOVED

**Vulnerability**: `CodeRunner._run_local()` executed candidate Python code on the backend host
via `subprocess.run(["python", fname])` with no sandboxing, no resource limits, and full system
access. This allowed untrusted candidate code to read files, exfiltrate data, and spawn processes
on the server.

**Remediation**: The local subprocess fallback has been **removed entirely** from
`backend/app/services/code_runner.py`.
- The `_run_local()` method has been deleted from the codebase.
- When no Judge0 API key is configured, `CodeRunner.run()` returns a controlled error:
  `"Code execution service is not configured. Contact support to enable coding challenges."`
- The Judge0 sandbox execution path is preserved for when an API key is properly configured.

**Current behavior**:
- Code execution without Judge0 configured: **Fails safely** — returns error message, no code runs
- Code execution with Judge0 configured: **Uses remote sandbox** (existing path, unchanged)
- Direct host execution of candidate code: **Not possible** (no reachable path)

## Phase A Remediations (Current)

### 3. Exam Submission Ownership — FIXED

`POST /exam/submit` now verifies that the stored in-memory exam belongs to the authenticated
user before grading, returning the existing `404 Exam not found or expired` response for missing
or cross-user exam IDs. The exam system remains in-memory as documented; this change only closes
the ownership check.

### 4. Video Question Audio Ownership — FIXED

`GET /video/question/{question_id}/audio` now requires the existing authenticated-user dependency
and resolves the question through its interview session owner before invoking TTS. Missing,
cross-user, and unauthenticated access cannot trigger audio generation.

### 5. Email Verification at Signup — FIXED

Signup now creates users as unverified, stores an OTP using the existing verification fields, sends
the OTP through the existing email provider, and returns no access or refresh token. Login, refresh,
the shared current-user dependency, and the existing WebSocket handshake reject unverified accounts.
Successful OTP verification marks the correct user verified and returns the normal authenticated
token response. The frontend preserves only the pending verification email in session storage so a
verification-page reload can continue the flow; the OTP and authentication tokens are not stored
there, and the pending email is cleared after successful verification.

Focused regression coverage for these remediations is in
`backend/tests/test_security_remediation.py`. The focused suite has 16 passing tests and the full
backend suite has 51 passing tests after implementation.

The following security work remains open and is intentionally not part of this checkpoint:

- Rate limiting and abuse controls
- Browser token storage and session hardening
- Upload limits and media validation
- WebSocket active-user authorization
- Raw exception sanitization
- OTP enumeration and brute-force protection
- Startup schema mutation and migration hardening

## Remaining Security Risks (Future Phases)

- **No password-reset flow**: A proper email-based password-reset mechanism is not yet implemented.
  This will be addressed in a future authentication-hardening phase with token-based flows, rate
  limiting, and email verification.
- **No Judge0/isolate service configured**: Code execution requires a configured Judge0 API key or
  equivalent isolated execution service for production use. This must be set up via environment
  variables before the coding functionality can operate in production.
- **Refresh token storage**: JWT refresh tokens are stored in `localStorage` without rotation/revocation
  (identified as a high-priority future hardening item).
- **No rate limiting**: Auth and AI endpoints have no rate limiting (identified as a future item).
- **No XSS protections discussed**: JWT access tokens in localStorage expose the application to
  cross-site scripting (identified as a future item).

## Conventions Used in This Document

- **[IMPLEMENTED]**: The change has been made and verified in the current codebase.
- **[PARTIAL]**: The change has been started but not fully completed or verified.
- **[FUTURE]**: The item is planned for a future phase but not yet implemented.
- **[IDEA]**: A noted possibility or design suggestion; no commitment to implementation.

---

For further details on specific components, see:
- `docs/CODING_SYSTEM.md` — Code execution security and sandbox requirements
- `docs/ARCHITECTURE.md` — Current vs target architecture, security posture summary
- `docs/VIDEOINTERVIEW.md` — Video interview security considerations (non-goals)
- `docs/COMPANY_PLATFORM.md` — ProctoAI Hire data isolation requirements