"""Initial schema migration: full relational foundation.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-11-18 22:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Schools
    op.create_table(
        "schools",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_schools_slug", "schools", ["slug"], unique=True)
    op.create_index("ix_schools_code", "schools", ["code"], unique=True)

    # 2. Classrooms
    op.create_table(
        "classrooms",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=20), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("school_id", "name", "academic_year", name="uq_classroom_school_name_year"),
    )
    op.create_index("ix_classrooms_school_id", "classrooms", ["school_id"])

    # 3. Learners
    op.create_table(
        "learners",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", sa.String(length=36), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_ref", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("school_id", "external_ref", name="uq_learner_school_external_ref"),
    )
    op.create_index("ix_learners_school_id", "learners", ["school_id"])
    op.create_index("ix_learners_classroom_id", "learners", ["classroom_id"])
    op.create_index("ix_learners_external_ref", "learners", ["external_ref"])

    # 4. Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 5. School Memberships
    op.create_table(
        "school_memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="teacher"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("school_id", "user_id", name="uq_school_user_membership"),
    )
    op.create_index("ix_school_memberships_school_id", "school_memberships", ["school_id"])
    op.create_index("ix_school_memberships_user_id", "school_memberships", ["user_id"])

    # 6. Class Memberships
    op.create_table(
        "class_memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", sa.String(length=36), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("classroom_id", "user_id", name="uq_class_user_membership"),
    )
    op.create_index("ix_class_memberships_classroom_id", "class_memberships", ["classroom_id"])
    op.create_index("ix_class_memberships_user_id", "class_memberships", ["user_id"])

    # 7. Topics
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("grade_level", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("school_id", "code", name="uq_topic_school_code"),
    )
    op.create_index("ix_topics_school_id", "topics", ["school_id"])

    # 8. Assessments
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", sa.String(length=36), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="imported"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_assessments_school_id", "assessments", ["school_id"])
    op.create_index("ix_assessments_classroom_id", "assessments", ["classroom_id"])

    # 9. Questions
    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("question_ref", sa.String(length=50), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_kind", sa.String(length=50), nullable=False),
        sa.Column("expected_answer", sa.String(length=100), nullable=False),
        sa.Column("max_marks", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column("order_num", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("assessment_id", "question_ref", name="uq_assessment_question_ref"),
    )
    op.create_index("ix_questions_assessment_id", "questions", ["assessment_id"])
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])

    # 10. Attempts
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_id", sa.String(length=36), sa.ForeignKey("learners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.String(length=100), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("awarded_marks", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
        sa.Column("scoring_version", sa.String(length=20), nullable=False, server_default="v1.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "question_id", "assessment_id", name="uq_attempt_learner_question_sitting"),
    )
    op.create_index("ix_attempts_assessment_id", "attempts", ["assessment_id"])
    op.create_index("ix_attempts_learner_id", "attempts", ["learner_id"])

    # 11. Gap Evidence
    op.create_table(
        "gap_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_id", sa.String(length=36), sa.ForeignKey("learners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("awarded_marks", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
        sa.Column("possible_marks", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
        sa.Column("assessed_items_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unattempted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("rule_version", sa.String(length=20), nullable=False, server_default="v1.0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "assessment_id", "topic_id", name="uq_gap_evidence_learner_assessment_topic"),
    )
    op.create_index("ix_gap_evidence_school_id", "gap_evidence", ["school_id"])
    op.create_index("ix_gap_evidence_assessment_id", "gap_evidence", ["assessment_id"])
    op.create_index("ix_gap_evidence_learner_id", "gap_evidence", ["learner_id"])

    # 12. Evidence Attempts join
    op.create_table(
        "evidence_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("gap_evidence_id", sa.String(length=36), sa.ForeignKey("gap_evidence.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_evidence_attempts_gap_id", "evidence_attempts", ["gap_evidence_id"])

    # 13. Teacher Decisions
    op.create_table(
        "teacher_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gap_evidence_id", sa.String(length=36), sa.ForeignKey("gap_evidence.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("corrected_topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_teacher_decisions_gap_id", "teacher_decisions", ["gap_evidence_id"])

    # 14. Support Groups
    op.create_table(
        "support_groups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", sa.String(length=36), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 15. Group Members
    op.create_table(
        "group_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("support_group_id", sa.String(length=36), sa.ForeignKey("support_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_id", sa.String(length=36), sa.ForeignKey("learners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gap_evidence_id", sa.String(length=36), sa.ForeignKey("gap_evidence.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("support_group_id", "learner_id", name="uq_group_learner"),
    )

    # 16. Support Plans
    op.create_table(
        "support_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("support_group_id", sa.String(length=36), sa.ForeignKey("support_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("current_version_id", sa.String(length=36), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 17. Plan Versions
    op.create_table(
        "plan_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("support_plan_id", sa.String(length=36), sa.ForeignKey("support_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_num", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("practice_items", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("support_plan_id", "version_num", name="uq_plan_version_num"),
    )

    # 18. Approved Snippets
    op.create_table(
        "approved_snippets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("source_ref", sa.String(length=100), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approved_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 19. Plan Sources
    op.create_table(
        "plan_sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("plan_version_id", sa.String(length=36), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snippet_id", sa.String(length=36), sa.ForeignKey("approved_snippets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("citation_note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 20. Approvals
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("plan_version_id", sa.String(length=36), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approval_hash", sa.String(length=64), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 21. Assignments
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_version_id", sa.String(length=36), sa.ForeignKey("plan_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 22. Assignment Recipients
    op.create_table(
        "assignment_recipients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assignment_id", sa.String(length=36), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learner_id", sa.String(length=36), sa.ForeignKey("learners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("assignment_id", "learner_id", name="uq_assignment_learner"),
    )

    # 23. Reassessments
    op.create_table(
        "reassessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_recipient_id", sa.String(length=36), sa.ForeignKey("assignment_recipients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_version_id", sa.String(length=36), sa.ForeignKey("plan_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quiz_version", sa.String(length=50), nullable=False, server_default="quiz-v1"),
        sa.Column("submission_state", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("teacher_decision", sa.String(length=50), nullable=True),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 24. Reassessment Responses
    op.create_table(
        "reassessment_responses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reassessment_id", sa.String(length=36), sa.ForeignKey("reassessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_ref", sa.String(length=50), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.String(length=100), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("awarded_marks", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 25. Jobs
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("heartbeat", sa.DateTime(), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_jobs_school_id", "jobs", ["school_id"])
    op.create_index("ix_jobs_request_hash", "jobs", ["request_hash"])

    # 26. Outbox Events
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 27. Idempotency Records
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("school_id", "actor_id", "operation", "idempotency_key", name="uq_idempotency_scoped_key"),
    )

    # 28. Audit Events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_school_id", "audit_events", ["school_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])


def downgrade() -> None:
    tables = [
        "audit_events",
        "idempotency_records",
        "outbox_events",
        "jobs",
        "reassessment_responses",
        "reassessments",
        "assignment_recipients",
        "assignments",
        "approvals",
        "plan_sources",
        "approved_snippets",
        "plan_versions",
        "support_plans",
        "group_members",
        "support_groups",
        "teacher_decisions",
        "evidence_attempts",
        "gap_evidence",
        "attempts",
        "questions",
        "assessments",
        "topics",
        "class_memberships",
        "school_memberships",
        "users",
        "learners",
        "classrooms",
        "schools",
    ]
    for table in tables:
        op.drop_table(table)
