"""Central API Router compiling all sub-module routes under /v1."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.classrooms.router import router as classrooms_router
from app.modules.evidence.router import router as evidence_router
from app.modules.imports.router import router as imports_router
from app.modules.jobs.router import router as jobs_router
from app.modules.plans.router import router as plans_router
from app.modules.reassessments.router import router as reassessments_router
from app.modules.audit.router import router as audit_router
from app.modules.demo.router import router as demo_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(classrooms_router)
api_router.include_router(imports_router)
api_router.include_router(jobs_router)
api_router.include_router(evidence_router)
api_router.include_router(plans_router)
api_router.include_router(reassessments_router)
api_router.include_router(audit_router)
api_router.include_router(demo_router)
