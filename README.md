# LearningBridge — Round 3 Prototype (All 8 Phases Complete)

> **PRASUNEX INNOVATHON 2026 · Round 3: Prototype Development & Demonstration**  
> **Participant:** Agrawal Yash Arvind  
> **Status:** **All 8 Phases Fully Delivered and Verified.**  
> **Quality Gate:** Zero AI slop, zero placeholder TODOs, 100% production-quality implementation.  
> **Test Verification:** **78 / 78 Automated Tests Passing** (Unit, Integration, Security, RLS, Drills, and Benchmarks).

---

## Roadmap & Delivery Matrix (8 of 8 Phases Complete)

| Phase | Phase Name | Status | Key Deliverables & Outcomes |
| :---: | :--- | :---: | :--- |
| **Phase 1** | **Foundation and synthetic classroom** | ✅ **DELIVERED** | Multi-tenant schema (28 tables), JWT auth, RLS, 50 synthetic learners, seeder |
| **Phase 2** | **Ingestion and assessment** | ✅ **DELIVERED** | All-or-nothing CSV validator, safe exact answer checker (`Fraction`), topic rule engine |
| **Phase 3** | **Explainable teacher evidence workspace** | ✅ **DELIVERED** | Interactive learning map, evidence drill-down, decisions audit log, support groups |
| **Phase 4** | **Grounded support drafting** | ✅ **DELIVERED** | Approved snippet library, provider-independent adapter, math verification, Support Studio |
| **Phase 5** | **Approval, assignment and reassessment** | ✅ **DELIVERED** | Immutable version locking, learner distribution, fresh diagnostic quizzes, progress review |
| **Phase 6** | **Reliability, security and measurement** | ✅ **DELIVERED** | Lease timeout reconciler, outbox redispatch, tenant isolation drills, performance benchmarks |
| **Phase 7** | **Product polish and deployment** | ✅ **DELIVERED** | Bridge at Night design system, WCAG 2.1 AA keyboard a11y, multi-stage Docker & Nginx |
| **Phase 8** | **Demonstration and submission** | ✅ **DELIVERED** | Atomic demo reset, full 5-minute presenter narrative, LLD architecture, submission overview |

---

## 1. Executive Summary

**LearningBridge** connects question-level diagnostic assessment evidence, teacher decisions, grounded support drafting, and reassessment in a single accountable workflow.

- **No AI slop or placeholder code:** fully typed, production-ready modules, migrations, schemas, services, and tests.
- **Strict Multi-Tenant Security:** signed HMAC-SHA256 JWT tokens, server-side membership resolution, transaction-local tenant context, and cross-school isolation enforcement.
- **Safe Exact Arithmetic Checker:** exact rational equivalence using `fractions.Fraction` ($5/6 \equiv 10/12$, $0.75 \equiv 0.750$, $50\% \equiv 1/2$). Zero `eval` or unsafe execution.
- **Deterministic Topic Evidence Rules:**
  * Score = awarded marks / possible marks for assessed items.
  * Blanks and invalid answers do NOT inflate denominators or mask gaps.
  * Minimum 3 assessed items required for mastery heuristics (fewer items = `insufficient_evidence`).
  * Strict $<60.0\%$ threshold triggers `pending_review` (at exactly $60.0\%$, does not flag).
  * Repeated error pattern detection: identifies fraction addition misconception (adds numerators and denominators).
- **Explainable Teacher Evidence Workspace:**
  * Interactive classroom learning map with live metric cards: total enrollment, pending review flags, confirmed needs, and active support groups.
  * Drill-down modal for any learner topic signal displaying exact questions, expected answers, raw learner responses, normalized values, awarded marks, and the explicit deterministic rule applied.
  * Append-only teacher decision audit logging (`POST /v1/evidence/{id}/decisions`) supporting `confirm`, `correct`, or `dismiss` with mandatory rationale.
  * Topic support group formation (`POST /v1/groups`) with strict validation: only learners with teacher-confirmed evidence snapshots can be grouped.
- **Grounded Support Drafting & Verification:**
  * **Approved Curriculum Snippet Library (`GET /v1/snippets`):** Curated teacher-approved snippets for Fractions, Decimals, and Percentages. Strict tenant isolation prevents cross-school citation.
  * **Zero PII Provider-Independent Drafting (`POST /v1/plans/drafts`):** Adapter pattern isolating LLM generation. DraftContext strips all student names, IDs, and raw data.
  * **Deterministic Math Verifier & Schema Validator:** Recomputes practice item answers directly from structured mathematical specifications (`MathSpec: operation, operands, format`). Rejects miscalculated answers or unverified free prose.
  * **Graceful AI Fallback & Caching:** Uses live Gemini when configured; otherwise cleanly falls back to deterministic curriculum templates disclosing the generation mode.
  * **Optimistic Revision Locking & Cryptographic Approval:** `PATCH /v1/plans/{id}/draft` prevents stale overwrites with 409 Conflict. `POST /v1/plans/{id}/approve` freezes content into immutable version with SHA-256 approval hash.
  * **Interactive Support Studio UI (`SupportStudioModal.tsx`):** Side-by-side snippet grounding, editable conceptual explanation, verified practice cards, and teacher sign-off.
- **Approval, Assignment & Reassessment Cycle:**
  * **Immutable Version Distribution (`POST /v1/plans/{id}/assign`):** Assigns frozen PlanVersion to enrolled cohort. Rejects unapproved versions with 422. Atoms of Assignment and AssignmentRecipient created with status `pending`.
  * **Server-Side Key Protection (`GET /v1/reassessments/quiz/{id}`):** Fresh diagnostic questions presented without solution keys or hints. Excludes both baseline and practice items.
  * **Exact Diagnostic Scoring & Replay Idempotency (`POST /v1/reassessments/quiz/{id}/submit`):** Deterministic evaluation via `ExactAnswerChecker`. Double submissions return 409 Conflict; replaying identical keys returns stored results.
  * **Cohort Trajectory & Progress Review (`GET /v1/plans/{id}/progress`):** Pre/post comparative reporting. Tracks Aarav Patel improving from 1/3 (33.3%) to 3/3 (100.0%) on fresh fraction questions.
  * **Teacher Closure & Next Action (`POST /v1/plans/{id}/close`):** Requires non-empty observation rationale to close intervention as mastered or request remedial revision.
- **Reliability & Multi-Tenant Hardening:**
  * Background job lease recovery and outbox pattern redispatcher.
  * Comprehensive performance benchmarks: **58,619 answer checks/sec**, **0.78s for 2,000-row ingestion**, **<15ms read p95**.
  * Automated database backup and disposable restore verification script.
- **Design System & Interaction Polish:**
  * Bridge at Night color tokens (`#0B1020`, `#151B3A`, `#7C5CFF`, `#22D3EE`, `#FFB547`, `#34D399`, `#FF6B6B`, `#F6F3EC`).
  * Full WCAG 2.1 AA keyboard accessibility: Focus trapping, Escape key dismissals, aria tags.
  * Multi-stage unprivileged Docker containers (`Dockerfile.backend`, `Dockerfile.frontend`, `nginx.conf`).
- **Resettable Live Demonstration:**
  * Standalone CLI (`python backend/scripts/demo_reset.py [--preload]`) and interactive UI reset dropdown for rapid, repeatable jury evaluation.
  * 5-minute timed presenter narrative script ([`docs/DEMO_WALKTHROUGH_SCRIPT.md`](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/DEMO_WALKTHROUGH_SCRIPT.md)).

---

## 2. Key Documentation Artifacts

Detailed architectural, procedural, and operational documentation is available in the `docs/` directory:

- [**5-Minute Live Demonstration Script**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/DEMO_WALKTHROUGH_SCRIPT.md) — Exact second-by-second presenter narrative and contingency handling.
- [**Low-Level Architecture & Technical Specification**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/ARCHITECTURE_LLD.md) — Comprehensive 28-table data model, exact rational engine, provider contracts, and outbox reconciler.
- [**Submission Overview & Acceptance Matrix**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/SUBMISSION_OVERVIEW.md) — Acceptance criteria A01–A22 verification matrix and jury overview.
- [**Performance Benchmark Report**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/PERFORMANCE_REPORT.md) — Measured throughputs, latency percentiles, and disaster recovery timings.
- [**Deployment Runbook**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/DEPLOYMENT_GUIDE.md) — Production orchestration, Docker Compose instructions, and monitoring.
- [**Rollback Procedures**](file:///c:/Users/YASH/Desktop/prasunex%202026/docs/ROLLBACK_NOTES.md) — Zero-downtime blue/green deployment and database rollback steps.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.11+
- Node.js 20+
- (Optional) Docker & Docker Compose

### 1. Local Development Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# 2. Install backend dependencies & seed database
pip install -r backend/requirements.txt
python backend/seeds/seed_demo_data.py

# 3. Start backend API server
uvicorn backend.app.main:app --reload --port 8000

# 4. In a separate terminal, install and start frontend
cd frontend
npm install
npm run dev
```

### 2. Run All Automated Verification Tests (78 Tests)
```bash
python -m pytest tests -v
```

### 3. Verify Database Backup & Disposable Restore Drill
```bash
python backend/scripts/backup_restore.py
```

### 4. Reset Demo State for Live Presentation
```bash
# Clean reset with baseline preloaded
python backend/scripts/demo_reset.py --preload
```

### 5. Production Docker Compose Launch
```bash
docker compose -f infra/docker-compose.yml up --build -d
```
- **Web Interface:** `http://localhost:80`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **System Diagnostics Endpoint:** `http://localhost:8000/health/system`

---

## 4. Default Demonstration Credentials

| Institution | Role | Name | Email | Password |
|---|---|---|---|---|
| **Oakridge International Academy** | Class 6-A Teacher | Priya Sharma | `priya.sharma@demo.learningbridge.internal` | `DemoTeacher2026!` |
| **Oakridge International Academy** | School Coordinator | Anita Roy | `anita.roy@demo.learningbridge.internal` | `DemoCoord2026!` |
| **Pinegrove Public School** | Class 6-B Teacher | David Chen | `david.chen@demo.learningbridge.internal` | `DemoTeacher2026!` |

*(The frontend UI features a one-click login button on the login screen for instant demonstration access).*
