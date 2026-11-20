"""Import and Job tracking schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RowErrorOut(BaseModel):
    """Specific row error returned on validation rejection."""

    row_num: int
    column: Optional[str] = None
    message: str


class ImportUploadResponse(BaseModel):
    """202 Accepted response upon receiving and registering a CSV import."""

    job_id: str
    status: str
    message: str
    idempotency_key: Optional[str] = None


class JobResultSummary(BaseModel):
    """Execution summary produced upon successful assessment import."""

    model_config = ConfigDict(extra="allow")

    assessment_id: Optional[str] = None
    assessment_title: Optional[str] = None
    classroom_id: Optional[str] = None
    rows_processed: int = 0
    questions_count: int = 0
    learners_count: int = 0
    topics_assessed: List[str] = Field(default_factory=list)
    pending_review_count: int = 0
    secure_count: int = 0
    insufficient_evidence_count: int = 0
    row_errors: Optional[List[RowErrorOut]] = None


class JobStatusResponse(BaseModel):
    """Status polling response for durable background jobs."""

    id: str
    kind: str
    status: str  # queued, running, succeeded, failed, retry_pending
    attempt_count: int
    max_attempts: int
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
