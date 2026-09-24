# Coding System — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Describes the coding-practice environment: what exists today and the intended secure,
evaluation-driven target. The product is **not** a LeetCode/Coding Ninjas re-creation. The
differentiator is **coding + reasoning + explanation + interview preparation**.

## 2. Target capabilities

- generate or select coding problems
- provide constraints + examples
- execute submissions **safely**
- evaluate correctness (test cases)
- evaluate complexity and code quality
- evaluate reasoning (explanation of approach)
- optionally ask follow-up questions
- integrate coding performance into the candidate's **broader skill profile**

## 3. Current implementation `[PARTIAL]`

Backend (`app/routers/coding.py`, `app/services/code_runner.py`, `app/services/ai_service.py`):

- `GET /coding/problems` — lists stored `CodingProblem` rows (filter difficulty/topic).
- `POST /coding/generate` — `AIService.generate_coding_problem` returns JSON used to create a
  `CodingProblem`. **Unvalidated beyond JSON parse; identical requests create duplicates.**
- `POST /coding/run` — `CodeRunner.run(code, language)`.
- `POST /coding/submit` — asks the LLM for a review (`review_code`), persisting a
  `CodeSubmission` with `stdout`, `stderr`, `runtime_ms`, `ai_review`, `code_quality_score`.
- `GET /coding/submissions` — user's submissions.

### Code execution — important caveats `[IMPLEMENTED]`

- `CodeRunner` supports many languages via **Judge0** (RapidAPI) — **only if an API key is
  configured**.
- **When no key is set, code execution fails safely** — returns a controlled error
  `"Code execution service is not configured. Contact support to enable coding challenges."`
  without executing any candidate code on the backend host.
- The local Python subprocess fallback (`_run_local`, `subprocess.run`) has been **removed**.
  There is no reachable path from the coding submission API to `subprocess.run()`,
  `os.system()`, `exec()`, `eval()`, or direct Python interpreter execution for
  candidate-submitted code.
- Judge0 mode uses base64 payloads and `wait=true` with a 30s HTTP timeout. No per-run CPU/memory
  caps configured client-side.

### Grading reality

- `CodingProblem.test_cases` and `CodeSubmission.passed_tests/total_tests` exist in the model but
  are **never populated**. "Correctness" is only the LLM's unverified `correct` boolean in the
  review JSON.
- No complexity evaluation, no reasoning evaluation, no follow-up questions.

Frontend (`src/pages/CodingPage.jsx`):

- Topic/difficulty pickers; "Generate Problem"; plain `textarea` editor (tab-key handled;
  no syntax highlighting); Run (shows stdout/stderr); Submit (shows AI review + quality score);
  collapsible hint.
- Languages offered: python, javascript, java, cpp.

## 4. Target V1 behavior

1. **Controlled problems:** stored, validated, versioned `CodingProblem` with real
   `test_cases`, constraints and a reference solution (see [Question System](QUESTION_SYSTEM.md)).
2. **Sandboxed execution:** code execution runs only inside a sandbox (container/isolate or a
   managed sandbox API such as Judge0). **No execution on the backend host.**
3. **Test-case grading:** deterministic pass/fail against hidden + public test cases; runtime and
   memory recorded; `correctness` derived from tests, not an LLM boolean.
4. **Review:** LLM review used only for quality/complexity/readability comments; the test score is
   the objective part.
5. **Reasoning step:** student explains approach (following interview conventions); the explanation
   is evaluated with the [Evaluation System](EVALUATION_SYSTEM.md) criteria.
6. **Profile integration:** coding results roll up into the skill profile (Phase 5 in
   [PRODUCT_ROADMAP](PRODUCT_ROADMAP.md)).

## 5. V1 scope decisions

- V1: one polished coding flow (select/generate → solve → run → submit → graded feedback +
  explanation). Multi-language breadth and long question chains are later.
- The mock-exam "coding" answer type (plain textarea, AI-graded) is a different, lighter-weight
  path and can remain separate in V1.
- **Code execution requires a configured sandbox service** (e.g. Judge0). Without configuration,
  submissions fail safely with a controlled error.

## 6. Open decisions

1. **Sandbox strategy:** self-hosted Docker/isolate service vs managed Judge0 (paid) vs both
   (primary/fallback). The local-subprocess fallback has been **removed** regardless.
2. Test-case authoring in V1: AI-generated-but-validated vs curated seed + AI for variants.
3. Which languages in V1 (Python only is the cheapest correct start; JS second).