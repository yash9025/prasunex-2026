"""Evidence and diagnostic summary response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class TopicOut(BaseModel):
    """Subject matter topic summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: Optional[str] = None
    grade_level: int


class EvidenceAttemptOut(BaseModel):
    """Supporting question response detail for explainable inspection."""

    attempt_id: str
    question_ref: str
    question_text: str
    answer_kind: str
    expected_answer: str
    raw_response: str
    normalized_value: Optional[str] = None
    outcome: str
    awarded_marks: Decimal
    max_marks: Decimal


class TeacherDecisionCreate(BaseModel):
    """Teacher action to confirm, correct, or dismiss a diagnostic evidence signal."""

    action: Literal["confirm", "correct", "dismiss"] = Field(
        ..., description="Action taken by teacher on the flagged evidence"
    )
    rationale: str = Field(
        ..., min_length=3, description="Pedagogical explanation for this decision"
    )
    corrected_topic_id: Optional[str] = Field(
        None, description="Target topic ID if action is 'correct'"
    )


class TeacherDecisionOut(BaseModel):
    """Persisted teacher decision log record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    gap_evidence_id: str
    actor_id: str
    actor_name: str
    action: str
    corrected_topic_id: Optional[str] = None
    rationale: str
    created_at: datetime


class GapEvidenceOut(BaseModel):
    """Diagnostic topic evidence snapshot for a learner."""

    id: str
    learner_id: str
    learner_ref: str
    learner_name: str
    topic_id: str
    topic_code: str
    topic_name: str
    awarded_marks: Decimal
    possible_marks: Decimal
    assessed_items_count: int
    unattempted_count: int
    invalid_count: int
    percentage: Optional[Decimal] = None
    rule_version: str
    status: str  # pending_review, confirmed, corrected, dismissed, insufficient_evidence
    suspected_pattern: Optional[str] = None
    supporting_attempts: List[EvidenceAttemptOut] = Field(default_factory=list)
    decisions: List[TeacherDecisionOut] = Field(default_factory=list)


class AssessmentOut(BaseModel):
    """Assessment sitting summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    classroom_id: str
    academic_year: str
    status: str
    created_at: datetime


class AssessmentEvidencePage(BaseModel):
    """Paginated collection of evidence snapshots for an assessment."""

    assessment: AssessmentOut
    total_records: int
    evidence: List[GapEvidenceOut]


class TopicEvidenceSummary(BaseModel):
    """Summary of evidence counts per curriculum topic."""

    topic_id: str
    topic_code: str
    topic_name: str
    pending_review_count: int = 0
    confirmed_count: int = 0
    secure_count: int = 0
    insufficient_evidence_count: int = 0
