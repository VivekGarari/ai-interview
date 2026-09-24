# Question System — ProctoAI

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Documents the **intended** question architecture: taxonomy, question blueprint, and the
generation → validation → dedup → persistence pipeline. It also states plainly what exists today
(near nothing of this) so nobody assumes it is built.

## 2. Status summary

| Concern | Status |
|---------|--------|
| Taxonomy (Domain → Topic → Subtopic → Skill/Concept → competencies) | `[PARTIAL]` — Domain/Topic/Subtopic foundation implemented; Skill/Concept and competencies not implemented |
| Question blueprint (versioned, structured entity) | `[PARTIAL]` — minimal Question/QuestionVersion foundation implemented |
| AI generation bounded by requirements | `[V1]` — **not implemented** (ad-hoc prompts today) |
| Schema validation of questions | `[V1]` — **not implemented** |
| Semantic validation | `[V1]` — **not implemented** |
| Deduplication | `[V1]` — **not implemented** |
| Persistence as reusable questions | `[PARTIAL]` — Question and QuestionVersion tables implemented; selection not implemented |
| Question selection for sessions | `[V1]` — **not implemented** |

## 3. Target: taxonomy

```
Domain
  → Topic
    → Subtopic
      → Skill / Concept
        → Expected competencies
```

The taxonomy is the *bounded vocabulary* that constrains question generation. A question may be
tagged with domain, topic, subtopic, difficulty, question type, and expected concepts. The same
taxonomy eventually powers the skill profile (mastery is tracked per Skill/Concept) and the
company assessment builder.

## 4. Target: question blueprint

A question should eventually carry structured information:

- `version`
- `text`
- `domain`
- `role` (`[IDEA]` — decide whether role is part of a question or only a selection filter)
- `language` (where applicable)
- `topic`
- `subtopic`
- `difficulty`
- `question_type` (concept / short-answer / coding / multi-round probe, etc.)
- `expected_concepts`
- `evaluation_criteria`
- `reference_answer` (where appropriate)
- `coding_constraints` (where appropriate)
- `test_cases` (where appropriate)
- `metadata` (content hash, status, source)
- `prompt_version` / `model` that generated it
- `content_hash`

## 5. Target: generation pipeline

```
Taxonomy
  → Question requirements (topic, difficulty, type, expected concepts)
    → LLM generation
      → Schema validation      (Pydantic / JSON Schema against the blueprint)
      → Semantic validation    (covered concepts present, coherent, not off-topic)
      → Deduplication          (content-hash / embedding-assisted, exact text match)
      → Persistence            (versioned row, approved state)
        → Question becomes usable
```

Two regimes over time:

1. **Generate-on-demand, then persist** (V1): a request produces a *draft* that is validated and
   stored; subsequent identical requests reuse the stored question. Sessions reference stored
   question versions rather than raw LLM text.
2. **Curated bank + batch generation** (`[FUTURE]`): larger pre-generated, pre-validated pools per
   topic; selection is deterministic (difficulty/intent) with optional LLM assistance only for
   fitting a specific profile.

### Anti-requirement

> The system should avoid generating an entirely new uncontrolled question every time a user
> requests one. Generation must be bounded by a controlled taxonomy and requirements.

## 6. Current implementation reality

- A minimal question store now exists through the `Domain`, `Topic`, `Subtopic`, `Question`, and
  `QuestionVersion` tables. Questions still live inside `SessionQuestion.question_text` rows for
  interview sessions because session integration is not implemented yet.
- `AIService.generate_question(role, interview_type, history, difficulty)` builds a free-text
  prompt and returns raw text. No validation, no dedup, no tagging, no versioning.
- `AIService.generate_coding_problem(...)` returns JSON that is immediately persisted as a
  `CodingProblem` — unvalidated beyond a JSON-parse attempt, and identical requests create
  duplicates.
- `AIService.generate_exam_questions(...)` generates a batch on the fly and stores it only in
  server memory for the life of that exam.
- The "taxonomy" is `frontend/src/data/options.js` (roles, coding topics, interview types) plus
  free-text backend strings. It is not authoritative and is not shared with the backend.
- `backend/app/models/question.py` contains the minimal taxonomy and question entities; services,
  question selection, and interview integration are not implemented yet.

## 7. V1 minimum

- Define the taxonomy shape and seed the top levels (domains/topics from `frontend/src/data/
  options.js` as a starting point).
- Implement the `Question`/`QuestionVersion` entities (see [Data Model](DATA_MODEL.md)).
- Wire interview start/coding/exam flows to a validated-question path (generate → validate →
  dedup → persist → select), with `content_hash` deduplication.
- Record generation metadata (`prompt_version`, `model`) for every persisted question.

## 8. Open decisions

1. Role-in-question vs role-as-filter (`[IDEA]`): simplest V1 default is filter-only.
2. Full manual curation review of AI questions before they are used, vs auto-approve with
   semantic-validation gates — affects launch speed vs quality.
3. Taxonomy source of truth: DB-seeded static tables vs config files — for V1, DB-seeded with
   seed scripts is simplest.
4. Question quality scoring: do we need a content-quality heuristic in V1 or is
   validate+dedup enough?