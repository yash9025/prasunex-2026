"""Schemas for assignment, fresh quiz taking, and pre/post progress review."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreateRequest(BaseModel):
    """Payload to distribute an approved plan version to support group learners."""

    plan_version_id: str = Field(..., description="ID of the approved PlanVersion to assign")
    due_date: Optional[datetime] = Field(None, description="Optional due date for assignment completion")


class RecipientOut(BaseModel):
    """Designated learner recipient of an intervention assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    learner_id: str
    learner_ref: str
    learner_name: str
    status: str  # pending, completed


class AssignmentOut(BaseModel):
    """Intervention assignment details and recipient progress."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    support_plan_id: str
    plan_version_id: str
    plan_version_num: int
    support_group_id: str
    support_group_name: str
    topic_code: str
    topic_name: str
    assigned_by_id: str
    assigned_by_name: str
    status: str  # active, completed, cancelled
    due_date: Optional[datetime]
    recipients: List[RecipientOut] = Field(default_factory=list)
    created_at: datetime


class QuizQuestionOut(BaseModel):
    """Question item provided to a student (strictly omits answer keys)."""

    question_ref: str
    question_text: str
    answer_kind: str
    max_marks: float = 1.0


class QuizOut(BaseModel):
    """Diagnostic quiz envelope for a student sitting."""

    recipient_id: str
    assignment_id: str
    learner_ref: str
    learner_name: str
    topic_code: str
    topic_name: str
    quiz_version: str
    status: str
    questions: List[QuizQuestionOut]


class QuizSubmissionAnswer(BaseModel):
    """Individual answer submitted by a student."""

    question_ref: str
    raw_response: str


class QuizSubmissionRequest(BaseModel):
    """Submission payload for an assignment quiz sitting."""

    submission_key: str = Field(..., min_length=5, max_length=100, description="Idempotency submission key")
    answers: List[QuizSubmissionAnswer] = Field(..., min_length=1)


class ScoredResponseItem(BaseModel):
    """Evaluated question response with transparent key and explanation."""

    question_ref: str
    question_text: str
    expected_answer: str
    raw_response: str
    normalized_value: Optional[str] = None
    outcome: str
    awarded_marks: float
    max_marks: float
    rationale: str


class QuizSubmissionResultOut(BaseModel):
    """Immediate diagnostic scoring outcome for a completed reassessment."""

    reassessment_id: str
    recipient_id: str
    learner_ref: str
    learner_name: str
    awarded_marks: float
    possible_marks: float
    percentage: float
    mastery_achieved: bool
    items: List[ScoredResponseItem]


class LearnerProgressDetail(BaseModel):
    """Comparative trajectory of an individual learner from baseline to fresh reassessment."""

    learner_id: str
    learner_ref: str
    learner_name: str
    baseline_awarded: float
    baseline_possible: float
    baseline_percentage: float
    reassessment_awarded: Optional[float] = None
    reassessment_possible: Optional[float] = None
    reassessment_percentage: Optional[float] = None
    status: str  # pending, completed
    is_completed: bool
    reassessment_items: List[ScoredResponseItem] = Field(default_factory=list)


class PlanProgressOut(BaseModel):
    """Aggregated pre/post intervention report across the support cohort."""

    plan_id: str
    plan_status: str
    support_group_id: str
    support_group_name: str
    topic_code: str
    topic_name: str
    assigned_version_num: int
    total_learners: int
    completed_count: int
    all_completed: bool
    learners: List[LearnerProgressDetail]


class PlanCloseRequest(BaseModel):
    """Teacher action deciding the next step based on reassessment evidence."""

    action: Literal["close", "request_revision"] = Field(
        ..., description="Whether to close the support cycle as mastered or request remedial revision."
    )
    rationale: str = Field(
        ..., min_length=10, max_length=1000, description="Mandatory teacher observation explaining the decision."
    )


class PlanCloseOut(BaseModel):
    """Result of closing or requesting revision on an intervention plan."""

    plan_id: str
    status: str
    action_taken: str
    rationale: str
    decided_at: datetime
