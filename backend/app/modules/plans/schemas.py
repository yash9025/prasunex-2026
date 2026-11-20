"""Support group and intervention schemas per Section 10 & 11 of the specification."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class GroupMemberCreate(BaseModel):
    """Specification of a learner to include in a support group."""

    learner_id: str = Field(..., description="Target learner identifier")
    gap_evidence_id: str = Field(..., description="Confirmed gap evidence snapshot ID")


class GroupMemberOut(BaseModel):
    """Enrolled member of a support group with snapshot evidence link."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    learner_id: str
    learner_ref: str
    learner_name: str
    gap_evidence_id: str


class SupportGroupCreate(BaseModel):
    """Payload to create a focused support cohort from confirmed evidence."""

    classroom_id: str = Field(..., description="Target classroom identifier")
    topic_id: str = Field(..., description="Target curriculum topic ID")
    name: str = Field(..., min_length=3, max_length=150, description="Support group title")
    members: List[GroupMemberCreate] = Field(
        ..., min_length=1, description="Explicit list of confirmed learners"
    )


class SupportGroupOut(BaseModel):
    """Support group details with enrolled members."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    classroom_id: str
    topic_id: str
    topic_code: str
    topic_name: str
    name: str
    created_by_id: str
    created_by_name: str
    members: List[GroupMemberOut] = Field(default_factory=list)
    created_at: datetime


# --- Phase 4: Grounded Support Drafting Schemas ---


class ApprovedSnippetOut(BaseModel):
    """Curated, teacher-verified lesson snippet."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    topic_id: str
    title: str
    content: str
    grade_level: int
    language: str
    source_ref: str
    is_approved: bool


class MathSpecSchema(BaseModel):
    """Deterministic mathematical specification for numeric items."""

    operation: Literal["add", "subtract", "multiply", "divide"]
    operands: List[str]
    answer_format: Literal["fraction", "decimal", "percentage", "integer"] = "fraction"


class PracticeItemSchema(BaseModel):
    """Verified practice item within an intervention plan."""

    item_num: int
    question_text: str
    math_spec: MathSpecSchema
    expected_answer: str
    rationale: str
    verified: bool = True
    verification_error: Optional[str] = None


class DraftGenerationRequest(BaseModel):
    """Request to generate a grounded intervention draft for a support group."""

    support_group_id: str = Field(..., description="ID of the target support group")
    source_snippet_ids: List[str] = Field(
        ..., min_length=1, description="List of approved snippet IDs to ground generation"
    )
    generation_mode: Literal["auto", "ai", "template"] = Field(
        default="auto", description="Provider mode (auto tries AI with template fallback)"
    )


class PlanVersionOut(BaseModel):
    """Immutable snapshot of intervention content and citations."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    support_plan_id: str
    version_num: int
    explanation: str
    practice_items: List[PracticeItemSchema]
    content_hash: str
    cited_snippets: List[ApprovedSnippetOut] = Field(default_factory=list)
    created_by_id: str
    created_by_name: str
    created_at: datetime


class SupportPlanOut(BaseModel):
    """Intervention support plan holding active draft and version history."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    support_group_id: str
    support_group_name: str
    topic_id: str
    topic_code: str
    topic_name: str
    status: str
    revision: int
    current_version_id: Optional[str] = None
    current_version: Optional[PlanVersionOut] = None
    generation_mode: Optional[str] = None
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PlanDraftUpdate(BaseModel):
    """Teacher modifications to draft explanation or practice items."""

    revision: int = Field(..., description="Optimistic locking revision counter")
    explanation: Optional[str] = Field(None, min_length=20, max_length=3000)
    practice_items: Optional[List[PracticeItemSchema]] = None


class PlanApprovalRequest(BaseModel):
    """Teacher sign-off freezing a plan version for learner assignment."""

    revision: int = Field(..., description="Optimistic locking revision counter")
    sign_off_responsibility: bool = Field(
        ..., description="Explicit acknowledgment that teacher takes responsibility for content."
    )


class ApprovalOut(BaseModel):
    """Approval audit record freezing a plan version."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_version_id: str
    approver_id: str
    approver_name: str
    approval_hash: str
    approved_at: datetime
