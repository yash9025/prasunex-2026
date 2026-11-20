"""Evidence and assessment models per Section 6 of the architecture plan.

Includes Topic, Assessment, Question, Attempt, GapEvidence, EvidenceAttempt, and TeacherDecision.
"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class Topic(Base, TimestampMixin):
    """Subject matter domain (e.g., Fractions, Decimals, Percentages)."""

    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    grade_level = Column(Integer, nullable=False, default=6)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_topic_school_code"),
    )

    questions = relationship("Question", back_populates="topic")


class Assessment(Base, TimestampMixin):
    """Classroom-level diagnostic assessment or sitting."""

    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    academic_year = Column(String(20), nullable=False, default="2026-2027")
    status = Column(String(50), nullable=False, default="imported")  # draft, importing, imported, archived
    revision = Column(Integer, nullable=False, default=1)

    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base, TimestampMixin):
    """Specific question within an assessment, mapped to a topic."""

    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True)
    question_ref = Column(String(50), nullable=False)  # e.g. Q1, Q2
    question_text = Column(Text, nullable=False)
    answer_kind = Column(String(50), nullable=False, default="numeric_fraction")  # numeric_fraction, numeric_decimal, numeric_percentage
    expected_answer = Column(String(100), nullable=False)
    max_marks = Column(Numeric(5, 2), nullable=False, default=1.0)
    order_num = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_ref", name="uq_assessment_question_ref"),
    )

    assessment = relationship("Assessment", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question")


class Attempt(Base, TimestampMixin):
    """Learner's response to an assessment question."""

    __tablename__ = "attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_response = Column(Text, nullable=False)
    normalized_value = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False)  # correct, incorrect, unattempted, invalid, requires_review
    awarded_marks = Column(Numeric(5, 2), nullable=False, default=0.0)
    scoring_version = Column(String(20), nullable=False, default="v1.0")

    __table_args__ = (
        UniqueConstraint("learner_id", "question_id", "assessment_id", name="uq_attempt_learner_question_sitting"),
    )

    question = relationship("Question", back_populates="attempts")


class GapEvidence(Base, TimestampMixin):
    """Topic-level evidence summary for a learner, showing aggregate marks and signals."""

    __tablename__ = "gap_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True)
    awarded_marks = Column(Numeric(5, 2), nullable=False, default=0.0)
    possible_marks = Column(Numeric(5, 2), nullable=False, default=0.0)
    assessed_items_count = Column(Integer, nullable=False, default=0)
    unattempted_count = Column(Integer, nullable=False, default=0)
    invalid_count = Column(Integer, nullable=False, default=0)
    percentage = Column(Numeric(5, 2), nullable=True)
    rule_version = Column(String(20), nullable=False, default="v1.0")
    status = Column(String(50), nullable=False, default="pending_review")  # pending_review, confirmed, corrected, dismissed, insufficient_evidence

    __table_args__ = (
        UniqueConstraint("learner_id", "assessment_id", "topic_id", name="uq_gap_evidence_learner_assessment_topic"),
    )

    decisions = relationship("TeacherDecision", back_populates="evidence", cascade="all, delete-orphan")


class EvidenceAttempt(Base, TimestampMixin):
    """Join table linking an immutable gap evidence snapshot to supporting question attempts."""

    __tablename__ = "evidence_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    gap_evidence_id = Column(String(36), ForeignKey("gap_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_id = Column(String(36), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, index=True)


class TeacherDecision(Base, TimestampMixin):
    """Teacher action confirming, correcting, or dismissing a detected learning need."""

    __tablename__ = "teacher_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    gap_evidence_id = Column(String(36), ForeignKey("gap_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # confirm, correct, dismiss
    corrected_topic_id = Column(String(36), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    rationale = Column(Text, nullable=False)

    evidence = relationship("GapEvidence", back_populates="decisions")
