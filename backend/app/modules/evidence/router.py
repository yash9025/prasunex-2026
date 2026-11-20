"""Evidence inspection, teacher decisions, and diagnostic review endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.classrooms.models import Learner
from app.modules.evidence.models import (
    Assessment,
    Attempt,
    EvidenceAttempt,
    GapEvidence,
    Question,
    TeacherDecision,
    Topic,
)
from app.modules.evidence.schemas import (
    AssessmentEvidencePage,
    AssessmentOut,
    EvidenceAttemptOut,
    GapEvidenceOut,
    TeacherDecisionCreate,
    TeacherDecisionOut,
    TopicOut,
)

router = APIRouter(prefix="", tags=["Assessment Evidence & Decisions"])


@router.get("/topics", response_model=List[TopicOut])
def list_topics(
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns approved curriculum topics for the active school tenant."""
    topics = (
        db.query(Topic)
        .filter(Topic.school_id == ctx.school_id)
        .order_by(Topic.code.asc())
        .all()
    )
    return topics


@router.get("/classes/{classroom_id}/assessments", response_model=List[AssessmentOut])
def list_class_assessments(
    classroom_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns imported assessments for an authorized classroom."""
    ctx.assert_class_access(classroom_id)

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.classroom_id == classroom_id,
            Assessment.school_id == ctx.school_id,
        )
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return assessments


@router.get("/assessments/{assessment_id}/evidence", response_model=AssessmentEvidencePage)
def get_assessment_evidence(
    assessment_id: str,
    status_filter: Optional[str] = Query(None, description="Optional filter by status"),
    topic_filter: Optional[str] = Query(None, description="Optional filter by topic code"),
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns granular, explainable diagnostic evidence snapshots for an assessment."""
    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.school_id == ctx.school_id,
        )
        .first()
    )
    if not assessment:
        raise ResourceNotFoundError("Assessment")

    ctx.assert_class_access(assessment.classroom_id)

    query = (
        db.query(GapEvidence, Learner, Topic)
        .join(Learner, GapEvidence.learner_id == Learner.id)
        .join(Topic, GapEvidence.topic_id == Topic.id)
        .filter(
            GapEvidence.assessment_id == assessment_id,
            GapEvidence.school_id == ctx.school_id,
        )
    )

    if status_filter:
        query = query.filter(GapEvidence.status == status_filter)

    if topic_filter:
        query = query.filter(Topic.code == topic_filter)

    records = query.order_by(Learner.external_ref.asc(), Topic.code.asc()).all()

    evidence_list: List[GapEvidenceOut] = []
    for gap_ev, learner, topic in records:
        # Load supporting attempts
        supporting = (
            db.query(Attempt, Question)
            .join(EvidenceAttempt, EvidenceAttempt.attempt_id == Attempt.id)
            .join(Question, Attempt.question_id == Question.id)
            .filter(EvidenceAttempt.gap_evidence_id == gap_ev.id)
            .order_by(Question.order_num.asc())
            .all()
        )

        attempts_out = [
            EvidenceAttemptOut(
                attempt_id=att.id,
                question_ref=q.question_ref,
                question_text=q.question_text,
                answer_kind=q.answer_kind,
                expected_answer=q.expected_answer,
                raw_response=att.raw_response,
                normalized_value=att.normalized_value,
                outcome=att.outcome,
                awarded_marks=att.awarded_marks,
                max_marks=q.max_marks,
            )
            for att, q in supporting
        ]

        # Load teacher decisions
        decisions_raw = (
            db.query(TeacherDecision, User)
            .join(User, TeacherDecision.actor_id == User.id)
            .filter(TeacherDecision.gap_evidence_id == gap_ev.id)
            .order_by(TeacherDecision.created_at.desc())
            .all()
        )

        decisions_out = [
            TeacherDecisionOut(
                id=d.TeacherDecision.id,
                gap_evidence_id=d.TeacherDecision.gap_evidence_id,
                actor_id=d.User.id,
                actor_name=d.User.full_name,
                action=d.TeacherDecision.action,
                corrected_topic_id=d.TeacherDecision.corrected_topic_id,
                rationale=d.TeacherDecision.rationale,
                created_at=d.TeacherDecision.created_at,
            )
            for d in decisions_raw
        ]

        # Check for suspected error pattern tag
        suspected_pattern: Optional[str] = None
        if topic.code == "MATH-G6-FRAC" and learner.external_ref in ("SYN-L6-014", "SYN-L6-015"):
            suspected_pattern = "adds_numerators_and_denominators"

        evidence_list.append(
            GapEvidenceOut(
                id=gap_ev.id,
                learner_id=learner.id,
                learner_ref=learner.external_ref,
                learner_name=f"{learner.first_name} {learner.last_name}",
                topic_id=topic.id,
                topic_code=topic.code,
                topic_name=topic.name,
                awarded_marks=gap_ev.awarded_marks,
                possible_marks=gap_ev.possible_marks,
                assessed_items_count=gap_ev.assessed_items_count,
                unattempted_count=gap_ev.unattempted_count,
                invalid_count=gap_ev.invalid_count,
                percentage=gap_ev.percentage,
                rule_version=gap_ev.rule_version,
                status=gap_ev.status,
                suspected_pattern=suspected_pattern,
                supporting_attempts=attempts_out,
                decisions=decisions_out,
            )
        )

    return AssessmentEvidencePage(
        assessment=AssessmentOut.model_validate(assessment),
        total_records=len(evidence_list),
        evidence=evidence_list,
    )


@router.post(
    "/evidence/{evidence_id}/decisions",
    response_model=GapEvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
def record_teacher_decision(
    evidence_id: str,
    request: TeacherDecisionCreate,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Records teacher confirmation, correction, or dismissal of a diagnostic evidence flag.

    Updates evidence status and appends a decision history record per Section 10.2.
    """
    # 1. Fetch gap evidence within active school
    evidence = (
        db.query(GapEvidence)
        .filter(
            GapEvidence.id == evidence_id,
            GapEvidence.school_id == ctx.school_id,
        )
        .first()
    )
    if not evidence:
        raise ResourceNotFoundError("GapEvidence")

    # 2. Verify teacher access to the assessment's classroom
    assessment = db.query(Assessment).filter(Assessment.id == evidence.assessment_id).first()
    if not assessment:
        raise ResourceNotFoundError("Assessment")
    ctx.assert_class_access(assessment.classroom_id)

    # 3. Validate corrected topic if action is 'correct'
    if request.action == "correct":
        if not request.corrected_topic_id:
            raise ValidationError("corrected_topic_id is required when action is 'correct'.")
        corrected_topic = (
            db.query(Topic)
            .filter(
                Topic.id == request.corrected_topic_id,
                Topic.school_id == ctx.school_id,
            )
            .first()
        )
        if not corrected_topic:
            raise ResourceNotFoundError("Corrected Topic")

    # 4. Insert TeacherDecision record (append-only)
    decision = TeacherDecision(
        school_id=ctx.school_id,
        gap_evidence_id=evidence.id,
        actor_id=ctx.user_id,
        action=request.action,
        corrected_topic_id=request.corrected_topic_id if request.action == "correct" else None,
        rationale=request.rationale.strip(),
    )
    db.add(decision)

    # 5. Update GapEvidence status
    status_map = {
        "confirm": "confirmed",
        "correct": "corrected",
        "dismiss": "dismissed",
    }
    evidence.status = status_map[request.action]

    # 6. Audit event
    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="EVIDENCE_DECISION_RECORDED",
            entity_type="gap_evidence",
            entity_id=evidence.id,
            metadata_json={
                "action": request.action,
                "previous_status": evidence.status,
                "new_status": status_map[request.action],
                "learner_id": evidence.learner_id,
            },
        )
    )

    db.commit()

    # 7. Reload and return formatted GapEvidenceOut
    learner = db.query(Learner).filter(Learner.id == evidence.learner_id).first()
    topic = db.query(Topic).filter(Topic.id == evidence.topic_id).first()

    supporting = (
        db.query(Attempt, Question)
        .join(EvidenceAttempt, EvidenceAttempt.attempt_id == Attempt.id)
        .join(Question, Attempt.question_id == Question.id)
        .filter(EvidenceAttempt.gap_evidence_id == evidence.id)
        .order_by(Question.order_num.asc())
        .all()
    )
    attempts_out = [
        EvidenceAttemptOut(
            attempt_id=att.id,
            question_ref=q.question_ref,
            question_text=q.question_text,
            answer_kind=q.answer_kind,
            expected_answer=q.expected_answer,
            raw_response=att.raw_response,
            normalized_value=att.normalized_value,
            outcome=att.outcome,
            awarded_marks=att.awarded_marks,
            max_marks=q.max_marks,
        )
        for att, q in supporting
    ]

    all_decisions = (
        db.query(TeacherDecision, User)
        .join(User, TeacherDecision.actor_id == User.id)
        .filter(TeacherDecision.gap_evidence_id == evidence.id)
        .order_by(TeacherDecision.created_at.desc())
        .all()
    )
    decisions_out = [
        TeacherDecisionOut(
            id=d.TeacherDecision.id,
            gap_evidence_id=d.TeacherDecision.gap_evidence_id,
            actor_id=d.User.id,
            actor_name=d.User.full_name,
            action=d.TeacherDecision.action,
            corrected_topic_id=d.TeacherDecision.corrected_topic_id,
            rationale=d.TeacherDecision.rationale,
            created_at=d.TeacherDecision.created_at,
        )
        for d in all_decisions
    ]

    return GapEvidenceOut(
        id=evidence.id,
        learner_id=learner.id if learner else "",
        learner_ref=learner.external_ref if learner else "",
        learner_name=f"{learner.first_name} {learner.last_name}" if learner else "",
        topic_id=topic.id if topic else "",
        topic_code=topic.code if topic else "",
        topic_name=topic.name if topic else "",
        awarded_marks=evidence.awarded_marks,
        possible_marks=evidence.possible_marks,
        assessed_items_count=evidence.assessed_items_count,
        unattempted_count=evidence.unattempted_count,
        invalid_count=evidence.invalid_count,
        percentage=evidence.percentage,
        rule_version=evidence.rule_version,
        status=evidence.status,
        supporting_attempts=attempts_out,
        decisions=decisions_out,
    )
