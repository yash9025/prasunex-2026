# PRASUNEX 2026 — LearningBridge prototype handoff

## Current instruction
The user asked to create a Desktop folder named `prasunex 2026` and a new chat carrying the project knowledge. Complete setup and wait for the user. Do not begin prototype implementation until the user continues.

## Competition and dates
The user provided the organizer's Round 3 qualification email on 18 November 2026. This is Prototype Development & Demonstration, not yet the final jury round.
- Development: 18 November 2026, 09:00 AM IST to 25 November 2026, 11:00 PM IST.
- Deliver a working prototype, MVP or proof of concept and demonstrate its practical application.
- Evaluation: functionality, technical execution, usability, innovation, applicability, scalability and demonstration quality.
- Teams shortlisted after Round 3 proceed to the online Final Jury Round on 1 December 2026.
- Participant name in the email: Agrawal Yash Arvind.

## Product and problem
Project: LearningBridge. Sponsor PRASUNEX is an AI-powered school ERP and education management platform connecting student records, attendance, learning and parent communication. Official context: https://prasunex.com/ . API access has NOT been verified.
Problem hypothesis: aggregate assessment scores conceal specific topic gaps. Teachers need help interpreting question-level evidence, preparing suitable practice and checking understanding after support.
Proposed distinction: a traceable complete cycle connecting evidence, teacher action and reassessment. Do not claim global uniqueness, proven learning improvements or a verified missing feature in PRASUNEX.

## MVP boundary
- One Class 6 maths class, 40 synthetic learners, fractions, decimals and percentages.
- CSV input with assessment questions, topic tags and learner answers.
- Deterministic answer checks and explainable topic flags.
- Teacher confirms, corrects or dismisses a suspected gap.
- Group learners with similar needs; draft focused activities using approved lesson material.
- Teacher edits and approves an immutable plan version before assignment.
- Fresh questions on the same topic attach to that plan; teacher closes or revises support.
- Exclude OCR, unrestricted free-form grading, a general AI tutor and live ERP integration from the initial build.
- Parent messages are optional teacher-reviewed drafts, not autonomous communication.

## Proposed architecture (design, not implemented code)
React + TypeScript teacher interface; FastAPI + Pydantic API; PostgreSQL for school-scoped records, evidence, jobs, plan versions and audit events; Celery workers with Redis broker for import and AI drafting jobs. Docker deployment. LLM provider behind a restricted adapter, no selected provider or credentials yet.
Interactive evidence reads and transactional approvals remain outside the LLM path. Workers persist results to PostgreSQL; Redis is not the durable source of job state. Start small and scale API and workers independently after measurements.

## Scoring and illustrative example
Topic score = sum awarded marks / sum possible marks for assessed items in a topic.
Initial configurable, versioned review heuristic: at least 3 assessed items and score below 60%. Fewer items means insufficient evidence. Unattempted answers stay a separate completion signal. This is not a mastery diagnosis.
Use strict, bounded rational/finite-decimal input grammar and exact arithmetic (e.g. Python Fraction from strings). Never eval user input. Free-form reasoning goes to the teacher.
Repeated-error tags require at least two supported matching patterns and teacher confirmation.
Synthetic example: total 7/10, but fractions 1/3 correct (33%), so review. Wrong answers: 1/2 + 1/3 = 2/5; 1/4 + 1/2 = 1/3. Actual correct answers are 5/6 and 3/4. Show sixths to explain the first sum, then reassess with fresh items. No improvement results exist.

## AI controls
Retrieve topic/grade-matched teacher-approved snippets, keep source IDs. Provider receives topic, grade and approved material, not learner names, IDs, raw CSV or raw responses. Treat snippet text as untrusted input, separate from instructions, with no model tool execution.
Output contract: topic_id, source_ids, explanation and three items with question, answer and rationale. Pydantic validates schema, sizes and counts. Recompute supported maths answer keys. Schema validity does not establish instructional quality: teacher review remains mandatory.
Network timeout, at most two transient retries, per-school quota and bounded concurrency. On failure offer a reviewed teacher-authored template, retain job status and reason. Cache candidate content by topic/content/prompt version/language, still requiring review before assignment.

## Workflow and API proposal
Plan states: draft, reviewed, assigned, reassessed, closed or needs_revision. Approval stores approved_version_id, actor and timestamp. An edit after approval creates a new draft; existing assignments retain their original version.
- POST /v1/imports: CSV + assessment reference, 202/job_id; validate file bounds and class access.
- GET /v1/jobs/{id}: 200/status; owning school only.
- POST /v1/plans/drafts: gap_id + source_ids, 202/job_id; confirmed gap required.
- POST /v1/plans/{id}/approve: expected_version, 200/version or 409 conflict.
- POST /v1/plans/{id}/assign: only approved current version.
- POST /v1/followups: approved_plan_id + answers, 201/evidence; scope and assignment checks.
Idempotency-Key on import/draft writes, request hashes and saved responses. Unique job keys, transactional writes and outbox/reconciliation for broker failures. No duplicate plans or assignments after replay.

## Data model and security
School, user, class_membership, learner, assessment, topic, question, attempt, gap_evidence, evidence_attempt join, support_plan, plan_version, reassessment, approved_snippet, job and audit_event.
school_id on every tenant record and composite foreign keys. Snapshot attempt/question IDs and rule version, immutable approved plan content, append-only audit events.
Verify signed token issuer/audience/expiry and authorized membership; do not trust school_id from an incoming body. PostgreSQL RLS, runtime DB role neither owner, superuser nor BYPASSRLS; transaction-local school context reset between pooled requests. Two-school isolation tests.
Roles: teacher assigned classes; coordinator authorized school oversight; worker tenant-scoped jobs. TLS, private authenticated data services, backups, secrets outside code, sanitized logs. No legal compliance certification is claimed.

## Eight-day proposed implementation plan
Days 1–2: schema, class access, CSV validation, synthetic fixtures; spike safe parsing and job recovery.
Days 3–4: exact answer checking, topic rules, evidence view.
Days 5–6: draft adapter, plan versioning, review, approval and assignment.
Days 7–8: fresh quiz, isolation tests, failure drills, demo rehearsal.
Gates: valid fixtures load without duplicates; scoring boundary/blank cases pass; stale assignments fail; fresh quiz attaches to approved plan. This is an estimate, not completed work.

## Validation and demo
Demonstrate import, inspect evidence, edit and approve a plan, assign it, then submit a fresh reassessment and review the next step. Include bad input, stale version, cross-school access, AI failure and duplicate replay cases.
Proposed load targets only: 2,000 supported response rows in under 10 seconds, read API p95 under 1 second, 50 concurrent read sessions on 2 vCPU / 4 GB RAM. Exclude LLM latency, report test query mix/data/error rate/duration, revise targets after profiling.
Pilot measures: teacher preparation time, draft edits/rejections, plan completion and fresh-question reasoning versus existing workflow. No causal claims from a small uncontrolled pilot.

## Design preferences
User strongly dislikes generic AI-looking slide templates and repeated three-card layouts. Latest redesign brief: The Bridge at Night. Navy 0B1020, indigo 151B3A, violet 7C5CFF, cyan 22D3EE for system, amber FFB547 for teacher decisions, mint 34D399 verified, coral FF6B6B failures. Light relief F6F3EC. Hero visuals, varied layouts, minimal body text, editable diagrams and notes containing full detail. Fallback fonts Segoe UI Semibold, Calibri, Consolas.
Translate these preferences into a polished, understandable teacher product. Clearly label synthetic records and proposed/mockup features; build real working behavior rather than a static demo presented as functional.

## Prior artifacts and unfinished deck export
Original workspace: C:/Users/YASH/Desktop/PPT_Automate.
Previously delivered Round 2 deck: output/LearningBridge_Round_2_Technical_Design.pptx.
Latest visual redesign was built and visually reviewed in the live artifact artifact_nZ2TEyEa47U845hB5tHO2bu0glXJ4t5n, but its final PPTX export hit an app quota and then an unsupported master color-map export issue. Do NOT call that latest file delivered or finalized.
Recovery files: round2-night-build/preserved-content.json, saved-live-state.json, deck-source.proto.json (binary protobuf despite extension), export-saved-deck.mjs. The latter has a colour-map repair in progress. No prototype implementation has started in this chat.
The new task is prototype preparation; do not silently resume the slide-export issue unless asked.

## Technical references checked previously
- https://fastapi.tiangolo.com/tutorial/background-tasks/
- https://docs.celeryq.dev/en/stable/userguide/tasks.html
- https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- https://docs.python.org/3/library/fractions.html
- https://docs.pydantic.dev/latest/concepts/models/

## Next action
Confirm the setup is complete and wait for the user to continue. Before implementation, inspect the new workspace, preserve existing files, and treat all of the above technical choices as the accepted starting proposal rather than proof of implemented functionality. Do not ask the user to repeat this history.
