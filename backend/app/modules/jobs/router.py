"""Job status inspection and background execution polling router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.imports.schemas import JobStatusResponse
from app.modules.jobs.models import Job

router = APIRouter(prefix="", tags=["Job Tracking & Diagnostics"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Polls background job status, sanitized and strictly tenant-scoped."""
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.school_id == ctx.school_id)
        .first()
    )
    if not job:
        raise ResourceNotFoundError("Job")

    return JobStatusResponse(
        id=job.id,
        kind=job.kind,
        status=job.status,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        failure_code=job.failure_code,
        failure_message=job.failure_message,
        result_summary=job.result_summary,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
