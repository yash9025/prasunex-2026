"""Classroom and learner API endpoints.

Enforces tenant scoping (school_id) and teacher class authorization.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.classrooms.models import Classroom, Learner, School
from app.modules.classrooms.schemas import (
    ClassOverviewMetric,
    ClassroomDetailOut,
    ClassroomOut,
    SchoolOut,
)

router = APIRouter(prefix="", tags=["Classrooms & Learners"])


@router.get("/schools", response_model=List[SchoolOut])
def list_schools(
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns schools where the current actor holds verified membership."""
    schools = (
        db.query(School)
        .filter(School.id.in_(ctx.authorized_school_ids), School.is_active == True)
        .all()
    )
    return schools


@router.get("/classes", response_model=List[ClassroomOut])
def list_assigned_classes(
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns classrooms assigned to the authenticated teacher within the active school."""
    query = db.query(Classroom).filter(Classroom.school_id == ctx.school_id)

    # Teachers only see their assigned classes; coordinators/admins see all classes in the school
    if ctx.role == "teacher":
        query = query.filter(Classroom.id.in_(ctx.authorized_class_ids))

    classrooms = query.all()

    result = []
    for c in classrooms:
        learner_count = db.query(Learner).filter(Learner.classroom_id == c.id).count()
        out = ClassroomOut(
            id=c.id,
            school_id=c.school_id,
            name=c.name,
            grade_level=c.grade_level,
            section=c.section,
            academic_year=c.academic_year,
            learner_count=learner_count,
        )
        result.append(out)

    return result


@router.get("/classes/{class_id}", response_model=ClassroomDetailOut)
def get_classroom_detail(
    class_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns classroom details and enrolled learners, strictly verifying class assignment."""
    ctx.assert_class_access(class_id)

    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == class_id, Classroom.school_id == ctx.school_id)
        .first()
    )
    if not classroom:
        raise ResourceNotFoundError("Classroom")

    learners = (
        db.query(Learner)
        .filter(Learner.classroom_id == class_id, Learner.school_id == ctx.school_id)
        .order_by(Learner.external_ref.asc())
        .all()
    )

    return ClassroomDetailOut(
        id=classroom.id,
        school_id=classroom.school_id,
        name=classroom.name,
        grade_level=classroom.grade_level,
        section=classroom.section,
        academic_year=classroom.academic_year,
        learner_count=len(learners),
        learners=learners,
    )


@router.get("/classes/{class_id}/overview", response_model=ClassOverviewMetric)
def get_class_overview(
    class_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns high-level class overview metrics for the active teacher per Section 7.1."""
    ctx.assert_class_access(class_id)

    total_learners = (
        db.query(Learner)
        .filter(Learner.classroom_id == class_id, Learner.school_id == ctx.school_id)
        .count()
    )
    synthetic_count = (
        db.query(Learner)
        .filter(
            Learner.classroom_id == class_id,
            Learner.school_id == ctx.school_id,
            Learner.is_synthetic == True,
        )
        .count()
    )

    from app.modules.evidence.models import Assessment, GapEvidence
    from app.modules.plans.models import SupportGroup

    active_assessments = (
        db.query(Assessment)
        .filter(Assessment.classroom_id == class_id, Assessment.school_id == ctx.school_id)
        .count()
    )

    pending_actions = (
        db.query(GapEvidence)
        .join(Assessment, GapEvidence.assessment_id == Assessment.id)
        .filter(
            Assessment.classroom_id == class_id,
            GapEvidence.school_id == ctx.school_id,
            GapEvidence.status == "pending_review",
        )
        .count()
    )

    confirmed_actions = (
        db.query(GapEvidence)
        .join(Assessment, GapEvidence.assessment_id == Assessment.id)
        .filter(
            Assessment.classroom_id == class_id,
            GapEvidence.school_id == ctx.school_id,
            GapEvidence.status == "confirmed",
        )
        .count()
    )

    groups_count = (
        db.query(SupportGroup)
        .filter(SupportGroup.classroom_id == class_id, SupportGroup.school_id == ctx.school_id)
        .count()
    )

    return ClassOverviewMetric(
        total_learners=total_learners,
        synthetic_count=synthetic_count,
        pending_actions_count=pending_actions,
        active_assessments_count=active_assessments,
        confirmed_count=confirmed_actions,
        groups_count=groups_count,
    )
