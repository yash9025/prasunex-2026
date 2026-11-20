"""Import endpoints: multipart CSV upload, job polling, and template download."""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import PayloadTooLargeError, ValidationError
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.imports.schemas import ImportUploadResponse
from app.modules.imports.service import ImportService

router = APIRouter(prefix="", tags=["CSV Assessment Import"])

CSV_TEMPLATE_CONTENT = (
    "learner_ref,question_ref,topic_ref,question_text,answer_kind,expected_answer,max_marks,response\n"
    "SYN-L6-001,Q1,MATH-G6-FRAC,Evaluate 1/2 + 1/3,numeric_fraction,5/6,1.0,5/6\n"
    "SYN-L6-001,Q4,MATH-G6-DEC,Calculate 0.25 + 0.5,numeric_decimal,0.75,1.0,0.75\n"
    "SYN-L6-001,Q7,MATH-G6-PCT,Calculate 50% of 80,numeric_integer,40,1.0,40\n"
)


@router.get("/imports/template", response_class=PlainTextResponse)
def download_csv_template():
    """Returns downloadable standard question-level assessment CSV template."""
    return PlainTextResponse(
        content=CSV_TEMPLATE_CONTENT,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="learningbridge_assessment_template.csv"'},
    )


@router.post(
    "/imports",
    response_model=ImportUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_assessment_csv(
    classroom_id: str = Form(..., description="Target classroom identifier"),
    assessment_title: str = Form(..., description="Assessment title / exam sitting"),
    file: UploadFile = File(..., description="Question-level CSV assessment file"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Accepts question-level CSV assessment for durable background scoring and evidence generation."""
    # Verify teacher authorization for target classroom
    ctx.assert_class_access(classroom_id)

    # Validate file size bound
    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_CSV_UPLOAD_SIZE_BYTES:
        raise PayloadTooLargeError(
            f"File size exceeds maximum allowable limit of {settings.MAX_CSV_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    if not file_bytes:
        raise ValidationError("Uploaded file is empty.")

    # Process import
    response = ImportService.submit_import(
        file_bytes=file_bytes,
        classroom_id=classroom_id,
        assessment_title=assessment_title,
        actor_id=ctx.user_id,
        school_id=ctx.school_id,
        idempotency_key=idempotency_key,
        db=db,
    )

    return response
