"""Support plan, versioning, approved snippet, and assignment models.

Enforces immutable versioning where approved versions and assignments are frozen.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class SupportGroup(Base, TimestampMixin):
    """Cohort of learners grouped for a common confirmed topic need."""

    __tablename__ = "support_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    plans = relationship("SupportPlan", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base, TimestampMixin):
    """Membership join linking learners to support groups with snapshot evidence reference."""

    __tablename__ = "group_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    support_group_id = Column(String(36), ForeignKey("support_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False, index=True)
    gap_evidence_id = Column(String(36), ForeignKey("gap_evidence.id", ondelete="RESTRICT"), nullable=False)

    __table_args__ = (
        UniqueConstraint("support_group_id", "learner_id", name="uq_group_learner"),
    )

    group = relationship("SupportGroup", back_populates="members")


class SupportPlan(Base, TimestampMixin):
    """Parent intervention plan holding draft/reviewed states and revision counter."""

    __tablename__ = "support_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    support_group_id = Column(String(36), ForeignKey("support_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="draft")  # draft, reviewed, assigned, reassessed, closed, needs_revision
    current_version_id = Column(String(36), nullable=True)
    revision = Column(Integer, nullable=False, default=1)

    group = relationship("SupportGroup", back_populates="plans")
    versions = relationship("PlanVersion", back_populates="plan", cascade="all, delete-orphan")


class PlanVersion(Base, TimestampMixin):
    """Immutable snapshot of intervention content: explanation, practice items, sources."""

    __tablename__ = "plan_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    support_plan_id = Column(String(36), ForeignKey("support_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    version_num = Column(Integer, nullable=False, default=1)
    explanation = Column(Text, nullable=False)
    practice_items = Column(JSON, nullable=False)  # List of items with question, answer, rationale
    content_hash = Column(String(64), nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    __table_args__ = (
        UniqueConstraint("support_plan_id", "version_num", name="uq_plan_version_num"),
    )

    plan = relationship("SupportPlan", back_populates="versions")
    approvals = relationship("Approval", back_populates="version", cascade="all, delete-orphan")


class ApprovedSnippet(Base, TimestampMixin):
    """Curated, teacher-verified lesson snippets used as grounded generation sources."""

    __tablename__ = "approved_snippets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    grade_level = Column(Integer, nullable=False, default=6)
    language = Column(String(10), nullable=False, default="en")
    source_ref = Column(String(100), nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)
    approved_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class PlanSource(Base, TimestampMixin):
    """Links an immutable PlanVersion to the specific ApprovedSnippets cited."""

    __tablename__ = "plan_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_version_id = Column(String(36), ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    snippet_id = Column(String(36), ForeignKey("approved_snippets.id", ondelete="RESTRICT"), nullable=False)
    citation_note = Column(String(255), nullable=True)


class Approval(Base, TimestampMixin):
    """Explicit sign-off by a teacher freezing a plan version for assignment."""

    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_version_id = Column(String(36), ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approval_hash = Column(String(64), nullable=False)
    approved_at = Column(DateTime, nullable=False)

    version = relationship("PlanVersion", back_populates="approvals")


class Assignment(Base, TimestampMixin):
    """Distribution of an approved plan version to designated learners."""

    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_version_id = Column(String(36), ForeignKey("plan_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active, completed, cancelled
    revision = Column(Integer, nullable=False, default=1)

    recipients = relationship("AssignmentRecipient", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentRecipient(Base, TimestampMixin):
    """Individual learner designated to complete the assigned practice."""

    __tablename__ = "assignment_recipients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, completed

    __table_args__ = (
        UniqueConstraint("assignment_id", "learner_id", name="uq_assignment_learner"),
    )

    assignment = relationship("Assignment", back_populates="recipients")
