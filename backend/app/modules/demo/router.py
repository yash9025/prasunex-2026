"""Demo environment reset endpoint adhering to Specification Section 15.1."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.demo.service import DemoResetService


router = APIRouter(prefix="/demo", tags=["Demonstration & Rehearsal"])


class DemoResetRequest(BaseModel):
    """Configuration options for demonstration reset."""

    preload_baseline: bool = False


@router.post("/reset")
def reset_demo_environment(
    req: DemoResetRequest = DemoResetRequest(),
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Restricted demonstration reset endpoint targeting the synthetic demo tenant."""
    return DemoResetService.reset_demo_tenant(
        db=db,
        school_id=ctx.school_id,
        actor_id=ctx.user_id,
        actor_name=ctx.full_name,
        preload_baseline=req.preload_baseline,
    )
