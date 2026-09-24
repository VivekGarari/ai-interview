# Company Platform — ProctoAI Hire `[FUTURE]`

Status legend: `[IMPLEMENTED]` / `[PARTIAL]` / `[V1]` / `[FUTURE]` / `[IDEA]`.

## 1. Purpose

Documents the separate long-term business/product idea: letting companies and startups host
technical assessments/interviews for candidates.

**Status: this entire product area is `[FUTURE]`. Nothing described here exists.** It is
documented to:
- record the intended model and product boundaries,
- keep the student product from accidentally growing company concepts,
- identify what belongs to later phases (Phase 8 – ProctoAI Hire).

## 2. Product concept

This is a **different user experience** from the student learning platform.

```
Company
  → Create Assessment
    → Configure Skills / Topics / Difficulty
      → Questions / Coding Problems
        → Invite Candidates
          → Candidate Assessment
            → Evaluation
              → Company Dashboard
                → Candidate Reports
```

## 3. Potential company functionality `[FUTURE]`

- company accounts
- assessment creation
- question selection/generation
- coding assessments
- written technical interviews
- video interviews
- candidate invitations
- candidate tracking
- evaluation reports
- comparison between candidates
- assessment analytics
- billing/subscriptions

## 4. Boundary rules (must hold in the target design)

1. **Do not merge the student and company products into one confusing domain model.**
2. They may share infrastructure and core assessment/evaluation engines (question store,
   evaluation engine, code sandbox, STT/TTS), but must have **clearly separated**:
   - product boundaries,
   - permissions,
   - workflows,
   - data access (strong candidate/company/assessment isolation).
3. Assessment/candidate data is confidential; see [Security](SECURITY.md) for the
   isolation requirements.

## 5. Conceptual brand split `[IDEA]`

- **ProctoAI Learn** → students/candidates → learning, preparation, interview simulation,
  personal progress.
- **ProctoAI Hire** → companies/recruiters → assessments, candidate evaluation, hiring workflows.

This split is a naming/organizing convention to keep the two products mentally and technically
separate; final naming is a product decision.

## 6. Conceptual data model (target only — NOT implemented)

```
Company-side future entities ([FUTURE]):
Organization
CompanyUser
Assessment
AssessmentQuestion
Candidate
Invitation
CandidateSubmission
CompanyEvaluation
```

See [Data Model](DATA_MODEL.md) for the full intended model and its status markers. Do not create
any of these tables simply because they are documented here.

## 7. Sequencing

- Phase 8 in [PRODUCT_ROADMAP](PRODUCT_ROADMAP.md).
- Prerequisites before starting: reliable question store + evaluation engine + code sandbox
  (from the student product), and completed auth/permission/isolations work.
- Payments/billing/subscriptions are Phase 9.

## 8. Open decisions

1. Assessment template model: fully AI-generated vs based on question bank selection (likely a
   hybrid — same engine as the student product, different permission/selection rules).
2. How companies access results: report links vs dashboard roles vs webhooks/ATS integrations.
3. Pricing/packaging — later; out of scope until the student product validates the core.