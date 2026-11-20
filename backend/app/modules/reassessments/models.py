"""Follow-up and reassessment models.

Captures fresh diagnostic responses against the assigned plan version.
"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class Reassessment(Base, TimestampMixin):
    """Fresh assessment submission linked directly to an assignment recipient."""

    __tablename__ = "reassessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_recipient_id = Column(String(36), ForeignKey("assignment_recipients.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_version_id = Column(String(36), ForeignKey("plan_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    quiz_version = Column(String(50), nullable=False, default="quiz-v1")
    submission_state = Column(String(50), nullable=False, default="completed")  # started, completed, scored
    teacher_decision = Column(String(50), nullable=True)  # close, revise
    decision_rationale = Column(Text, nullable=True)

    responses = relationship("ReassessmentResponse", back_populates="reassessment", cascade="all, delete-orphan")


class ReassessmentResponse(Base, TimestampMixin):
    """Individual item responses in a reassessment quiz."""

    __tablename__ = "reassessment_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reassessment_id = Column(String(36), ForeignKey("reassessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_ref = Column(String(50), nullable=False)
    raw_response = Column(Text, nullable=False)
    normalized_value = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False)  # correct, incorrect, invalid
    awarded_marks = Column(Numeric(5, 2), nullable=False, default=0.0)

    reassessment = relationship("Reassessment", back_populates="responses")
