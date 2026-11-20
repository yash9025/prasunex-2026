# LearningBridge — Data Model & Schema Specification

Adheres directly to Section 6 of the Implementation Plan (`LEARNINGBRIDGE_IMPLEMENTATION_PLAN.md`).

## Entity Summary

| Table | Tenant Key | Description | Key Constraints |
|---|---|---|---|
| `schools` | `id` | Tenant root (Oakridge, Pinegrove) | Unique `slug`, unique `code` |
| `classrooms` | `school_id` | Cohort / section (Grade 6-A, Grade 6-B) | Unique `(school_id, name, academic_year)` |
| `learners` | `school_id` | Enrolled synthetic student | Unique `(school_id, external_ref)`, `is_synthetic` flag |
| `users` | Global | Teacher and administrator accounts | Unique `email` |
| `school_memberships`| `school_id` | Associates user with school role | Unique `(school_id, user_id)` |
| `class_memberships` | `school_id` | Authorizes teacher to manage class | Unique `(classroom_id, user_id)` |
| `topics` | `school_id` | Subject topics (Fractions, Decimals, Percentages) | Unique `(school_id, code)` |
| `assessments` | `school_id` | Diagnostic assessment instance | Scoped to `classroom_id`, optimistic `revision` |
| `questions` | `school_id` | Assessment questions with answer kind & key | Unique `(assessment_id, question_ref)` |
| `attempts` | `school_id` | Question response snapshot with awarded marks | Unique `(learner_id, question_id, assessment_id)` |
| `gap_evidence` | `school_id` | Topic-level evidence & review status | Unique `(learner_id, assessment_id, topic_id)` |
| `teacher_decisions`| `school_id` | Append-only confirm/correct/dismiss actions | Foreign key to `gap_evidence_id` |
| `support_groups` | `school_id` | Cohort grouped for focused practice | Created by teacher for topic need |
| `group_members` | Join table | Links learners to support group | Unique `(support_group_id, learner_id)` |
| `support_plans` | `school_id` | Intervention parent record with states | Optimistic `revision` counter |
| `plan_versions` | Parent FK | Immutable intervention explanation & practice | Unique `(support_plan_id, version_num)` |
| `approved_snippets`| `school_id` | Curated lesson snippets library | Topic, grade, language, source reference |
| `plan_sources` | Parent FK | Links plan version to cited snippets | Immutable source citation snapshot |
| `approvals` | Parent FK | Formal teacher approval freezing plan version | Actor, timestamp, approval SHA-256 hash |
| `assignments` | `school_id` | Distribution of approved plan version | Scoped to `plan_version_id`, due date, revision |
| `assignment_recipients` | Join table | Assigned learners | Unique `(assignment_id, learner_id)` |
| `reassessments` | `school_id` | Fresh quiz submission linked to assignment | Status, teacher closure/revision rationale |
| `reassessment_responses`| Parent FK | Item responses in reassessment quiz | Outcome and awarded marks |
| `jobs` | `school_id` | Background import / drafting job tracking | Unique `request_hash`, heartbeat, retry count |
| `outbox_events` | `school_id` | Transactional outbox events for Redis broker | Dispatch status, retry count |
| `idempotency_records` | `school_id` | Deduplication table for imports & drafts | Unique `(school_id, actor_id, operation, key)` |
| `audit_events` | `school_id` | Append-only event log | Actor, action, entity, timestamp |
