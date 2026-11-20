"""Reassessment, Assignment, and Progress Review endpoints per Section 12 of the specification.

Enforces:
1. Assignments strictly require an explicitly approved PlanVersion.
2. Fresh diagnostic items exclude original baseline and practice questions.
3. Server-side key protection (keys are never exposed to learners during quiz sitting).
4. Submission idempotency and double-submission protection (409 Conflict).
5. Pre/post trajectory comparative reporting with teacher closure audit.
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom, Learner
from app.modules.evidence.models import GapEvidence, Topic
from app.modules.jobs.models import IdempotencyRecord
from app.modules.plans.models import (
    Approval,
    Assignment,
    AssignmentRecipient,
    PlanVersion,
    SupportGroup,
    SupportPlan,
)
from app.modules.reassessments.models import Reassessment, ReassessmentResponse
from app.modules.reassessments.question_bank import FreshQuestionBank
from app.modules.reassessments.schemas import (
    AssignmentCreateRequest,
    AssignmentOut,
    LearnerProgressDetail,
    PlanCloseOut,
    PlanCloseRequest,
    PlanProgressOut,
    QuizOut,
    QuizQuestionOut,
    QuizSubmissionRequest,
    QuizSubmissionResultOut,
    RecipientOut,
    ScoredResponseItem,
)
from app.modules.scoring.checker import ExactAnswerChecker

router = APIRouter(prefix="", tags=["Assignment & Reassessment"])


# =========================================================================
# Assignment Endpoints (Section 12.2)
# =========================================================================


@router.post(
    "/plans/{plan_id}/assign",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_intervention_assignment(
    plan_id: str,
    request: AssignmentCreateRequest,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Distributes an approved PlanVersion to support group learners.
    
    Invariants:
    1. Plan must exist in active school.
    2. Teacher must have classroom access.
    3. PlanVersion must be explicitly approved (Approval record exists).
    4. Group must have enrolled members.
    5. Creates Assignment and AssignmentRecipient records atomically.
    """
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.id == plan_id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        raise ResourceNotFoundError("SupportPlan")

    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    if not group:
        raise ResourceNotFoundError("SupportGroup")
    ctx.assert_class_access(group.classroom_id)

    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()

    # 1. Verify PlanVersion exists for this plan
    plan_version = (
        db.query(PlanVersion)
        .filter(PlanVersion.id == request.plan_version_id, PlanVersion.support_plan_id == plan.id)
        .first()
    )
    if not plan_version:
        raise ResourceNotFoundError("PlanVersion")

    # 2. Strict Invariant: PlanVersion must be APPROVED
    approval = (
        db.query(Approval)
        .filter(Approval.plan_version_id == plan_version.id)
        .first()
    )
    if not approval:
        raise ValidationError(
            f"Cannot assign unapproved plan version {plan_version.version_num}. Plan version must be approved by teacher first."
        )

    # 3. Verify group has enrolled members
    if not group.members:
        raise ValidationError("Cannot assign intervention to empty support group.")

    # 4. Create Assignment
    assignment = Assignment(
        school_id=ctx.school_id,
        plan_version_id=plan_version.id,
        assigned_by_id=ctx.user_id,
        due_date=request.due_date,
        status="active",
        revision=1,
    )
    db.add(assignment)
    db.flush()

    # 5. Create AssignmentRecipients and initial Reassessment placeholders
    recipients_out: List[RecipientOut] = []
    for gm in group.members:
        learner = db.query(Learner).filter(Learner.id == gm.learner_id).first()
        recipient = AssignmentRecipient(
            assignment_id=assignment.id,
            learner_id=gm.learner_id,
            status="pending",
        )
        db.add(recipient)
        db.flush()

        reassessment = Reassessment(
            school_id=ctx.school_id,
            assignment_recipient_id=recipient.id,
            assigned_version_id=plan_version.id,
            quiz_version="quiz-v1",
            submission_state="pending",
        )
        db.add(reassessment)

        recipients_out.append(
            RecipientOut(
                id=recipient.id,
                learner_id=learner.id,
                learner_ref=learner.external_ref,
                learner_name=f"{learner.first_name} {learner.last_name}",
                status=recipient.status,
            )
        )

    # 6. Update SupportPlan status
    plan.status = "assigned"
    plan.revision += 1
    plan.updated_at = datetime.now(timezone.utc)

    # 7. Audit Event
    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="ASSIGNMENT_CREATED",
            entity_type="assignment",
            entity_id=assignment.id,
            metadata_json={
                "support_plan_id": plan.id,
                "plan_version_id": plan_version.id,
                "version_num": plan_version.version_num,
                "recipient_count": len(recipients_out),
            },
        )
    )

    db.commit()

    return AssignmentOut(
        id=assignment.id,
        school_id=assignment.school_id,
        support_plan_id=plan.id,
        plan_version_id=plan_version.id,
        plan_version_num=plan_version.version_num,
        support_group_id=group.id,
        support_group_name=group.name,
        topic_code=topic.code,
        topic_name=topic.name,
        assigned_by_id=ctx.user_id,
        assigned_by_name=ctx.full_name,
        status=assignment.status,
        due_date=assignment.due_date,
        recipients=recipients_out,
        created_at=assignment.created_at,
    )


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves assignment status and recipient completion records."""
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.school_id == ctx.school_id)
        .first()
    )
    if not assignment:
        raise ResourceNotFoundError("Assignment")

    plan_ver = db.query(PlanVersion).filter(PlanVersion.id == assignment.plan_version_id).first()
    plan = db.query(SupportPlan).filter(SupportPlan.id == plan_ver.support_plan_id).first()
    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    ctx.assert_class_access(group.classroom_id)

    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()
    assigner = db.query(User).filter(User.id == assignment.assigned_by_id).first()

    recipients_out = []
    for r in assignment.recipients:
        learner = db.query(Learner).filter(Learner.id == r.learner_id).first()
        recipients_out.append(
            RecipientOut(
                id=r.id,
                learner_id=learner.id,
                learner_ref=learner.external_ref,
                learner_name=f"{learner.first_name} {learner.last_name}",
                status=r.status,
            )
        )

    return AssignmentOut(
        id=assignment.id,
        school_id=assignment.school_id,
        support_plan_id=plan.id,
        plan_version_id=plan_ver.id,
        plan_version_num=plan_ver.version_num,
        support_group_id=group.id,
        support_group_name=group.name,
        topic_code=topic.code,
        topic_name=topic.name,
        assigned_by_id=assigner.id if assigner else ctx.user_id,
        assigned_by_name=assigner.full_name if assigner else ctx.full_name,
        status=assignment.status,
        due_date=assignment.due_date,
        recipients=recipients_out,
        created_at=assignment.created_at,
    )


@router.get("/plans/{plan_id}/assignment", response_model=Optional[AssignmentOut])
def get_plan_assignment(
    plan_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves the active assignment for a plan if one has been distributed."""
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.id == plan_id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        raise ResourceNotFoundError("SupportPlan")

    assignment = (
        db.query(Assignment)
        .filter(Assignment.plan_version_id == plan.current_version_id)
        .order_by(Assignment.created_at.desc())
        .first()
    )
    if not assignment:
        return None

    return get_assignment(assignment.id, ctx, db)


# =========================================================================
# Reassessment Quiz Endpoints (Section 12.3)
# =========================================================================


@router.get("/reassessments/quiz/{recipient_id}", response_model=QuizOut)
def get_reassessment_quiz(
    recipient_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Provides fresh diagnostic quiz items for a recipient sitting.
    
    Guarantees:
    1. Server-side key protection: Answer keys and rationales are strictly OMITTED.
    2. Fresh questions: Items are distinct from baseline and practice items.
    """
    recipient = (
        db.query(AssignmentRecipient)
        .join(Assignment, AssignmentRecipient.assignment_id == Assignment.id)
        .filter(AssignmentRecipient.id == recipient_id, Assignment.school_id == ctx.school_id)
        .first()
    )
    if not recipient:
        raise ResourceNotFoundError("AssignmentRecipient")

    assignment = db.query(Assignment).filter(Assignment.id == recipient.assignment_id).first()
    plan_ver = db.query(PlanVersion).filter(PlanVersion.id == assignment.plan_version_id).first()
    plan = db.query(SupportPlan).filter(SupportPlan.id == plan_ver.support_plan_id).first()
    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()
    learner = db.query(Learner).filter(Learner.id == recipient.learner_id).first()

    # Load fresh questions
    fresh_items = FreshQuestionBank.get_fresh_items(topic.code)
    questions_out = [
        QuizQuestionOut(
            question_ref=item.question_ref,
            question_text=item.question_text,
            answer_kind=item.answer_kind,
            max_marks=item.max_marks,
        )
        for item in fresh_items
    ]

    return QuizOut(
        recipient_id=recipient.id,
        assignment_id=assignment.id,
        learner_ref=learner.external_ref,
        learner_name=f"{learner.first_name} {learner.last_name}",
        topic_code=topic.code,
        topic_name=topic.name,
        quiz_version="quiz-v1",
        status=recipient.status,
        questions=questions_out,
    )


@router.post("/reassessments/quiz/{recipient_id}/submit", response_model=QuizSubmissionResultOut)
def submit_reassessment_quiz(
    recipient_id: str,
    request: QuizSubmissionRequest,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Submits responses for a recipient reassessment quiz sitting.
    
    Guarantees:
    1. Submission idempotency: Replaying with same submission_key returns stored result.
    2. Double-submission protection: Re-submission with differing key without authorization returns 409 Conflict.
    3. Evaluated using ExactAnswerChecker with exact rational equivalence.
    4. Automatically updates recipient status, assignment completion, and plan status.
    """
    recipient = (
        db.query(AssignmentRecipient)
        .join(Assignment, AssignmentRecipient.assignment_id == Assignment.id)
        .filter(AssignmentRecipient.id == recipient_id, Assignment.school_id == ctx.school_id)
        .first()
    )
    if not recipient:
        raise ResourceNotFoundError("AssignmentRecipient")

    assignment = db.query(Assignment).filter(Assignment.id == recipient.assignment_id).first()
    plan_ver = db.query(PlanVersion).filter(PlanVersion.id == assignment.plan_version_id).first()
    plan = db.query(SupportPlan).filter(SupportPlan.id == plan_ver.support_plan_id).first()
    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()
    learner = db.query(Learner).filter(Learner.id == recipient.learner_id).first()

    reassessment = (
        db.query(Reassessment)
        .filter(Reassessment.assignment_recipient_id == recipient.id)
        .first()
    )
    if not reassessment:
        reassessment = Reassessment(
            school_id=ctx.school_id,
            assignment_recipient_id=recipient.id,
            assigned_version_id=plan_ver.id,
            quiz_version="quiz-v1",
            submission_state="pending",
        )
        db.add(reassessment)
        db.flush()

    # 1. Idempotency Check
    idempotency_rec = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.school_id == ctx.school_id,
            IdempotencyRecord.operation == f"quiz_submission_{recipient.id}",
            IdempotencyRecord.idempotency_key == request.submission_key,
        )
        .first()
    )
    if idempotency_rec:
        return QuizSubmissionResultOut(**idempotency_rec.response_body)

    # 2. Re-submission conflict protection
    if recipient.status == "completed":
        raise ConflictError(
            "Reassessment quiz has already been completed for this learner. Retakes require teacher authorization."
        )

    # 3. Grade each answer using ExactAnswerChecker
    scored_items: List[ScoredResponseItem] = []
    total_awarded = Decimal("0.0")
    total_possible = Decimal("0.0")

    # Clear any previous pending responses
    db.query(ReassessmentResponse).filter(ReassessmentResponse.reassessment_id == reassessment.id).delete()

    answer_map = {a.question_ref: a.raw_response for a in request.answers}
    fresh_items = FreshQuestionBank.get_fresh_items(topic.code)

    for item in fresh_items:
        raw_resp = answer_map.get(item.question_ref, "")
        scoring_res = ExactAnswerChecker.check_answer(
            raw_response=raw_resp,
            expected_answer=item.expected_answer,
            answer_kind=item.answer_kind,
            max_marks=item.max_marks,
        )

        db.add(
            ReassessmentResponse(
                reassessment_id=reassessment.id,
                question_ref=item.question_ref,
                raw_response=raw_resp,
                normalized_value=scoring_res.normalized_value,
                outcome=scoring_res.outcome.value,
                awarded_marks=scoring_res.awarded_marks,
            )
        )

        total_awarded += scoring_res.awarded_marks
        total_possible += Decimal(str(item.max_marks))

        scored_items.append(
            ScoredResponseItem(
                question_ref=item.question_ref,
                question_text=item.question_text,
                expected_answer=item.expected_answer,
                raw_response=raw_resp,
                normalized_value=scoring_res.normalized_value,
                outcome=scoring_res.outcome.value,
                awarded_marks=float(scoring_res.awarded_marks),
                max_marks=float(item.max_marks),
                rationale=item.rationale,
            )
        )

    percentage = round(float((total_awarded / total_possible) * 100), 2) if total_possible > 0 else 0.0
    mastery_achieved = percentage >= 60.0

    # 4. Update Reassessment & Recipient state
    reassessment.submission_state = "completed"
    recipient.status = "completed"

    # Check if all recipients for this assignment are completed
    pending_count = (
        db.query(AssignmentRecipient)
        .filter(AssignmentRecipient.assignment_id == assignment.id, AssignmentRecipient.status == "pending")
        .count()
    )
    if pending_count == 0:
        assignment.status = "completed"
        plan.status = "reassessed"

    result_payload = QuizSubmissionResultOut(
        reassessment_id=reassessment.id,
        recipient_id=recipient.id,
        learner_ref=learner.external_ref,
        learner_name=f"{learner.first_name} {learner.last_name}",
        awarded_marks=float(total_awarded),
        possible_marks=float(total_possible),
        percentage=percentage,
        mastery_achieved=mastery_achieved,
        items=scored_items,
    )

    # 5. Persist Idempotency Record
    req_hash = hashlib.sha256(
        json.dumps([a.model_dump() for a in request.answers], sort_keys=True).encode("utf-8")
    ).hexdigest()

    db.add(
        IdempotencyRecord(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            operation=f"quiz_submission_{recipient.id}",
            idempotency_key=request.submission_key,
            request_hash=req_hash,
            status_code=200,
            response_body=result_payload.model_dump(),
        )
    )

    # 6. Audit Event
    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="REASSESSMENT_SUBMITTED",
            entity_type="reassessment",
            entity_id=reassessment.id,
            metadata_json={
                "learner_ref": learner.external_ref,
                "percentage": percentage,
                "mastery_achieved": mastery_achieved,
            },
        )
    )

    db.commit()
    return result_payload


# =========================================================================
# Progress Review & Next Action Endpoints (Section 12.4)
# =========================================================================


@router.get("/plans/{plan_id}/progress", response_model=PlanProgressOut)
def get_plan_progress_report(
    plan_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Compares baseline diagnostic evidence with fresh post-intervention reassessment results."""
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.id == plan_id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        raise ResourceNotFoundError("SupportPlan")

    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    ctx.assert_class_access(group.classroom_id)
    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()

    # Find active assignment
    assignment = (
        db.query(Assignment)
        .filter(Assignment.plan_version_id == plan.current_version_id)
        .order_by(Assignment.created_at.desc())
        .first()
    )

    plan_ver = db.query(PlanVersion).filter(PlanVersion.id == plan.current_version_id).first()
    version_num = plan_ver.version_num if plan_ver else 1

    learners_progress: List[LearnerProgressDetail] = []
    completed_count = 0

    fresh_items_map = {it.question_ref: it for it in FreshQuestionBank.get_fresh_items(topic.code)}

    for gm in group.members:
        learner = db.query(Learner).filter(Learner.id == gm.learner_id).first()
        baseline_ev = db.query(GapEvidence).filter(GapEvidence.id == gm.gap_evidence_id).first()

        recipient = None
        reassessment = None
        if assignment:
            recipient = (
                db.query(AssignmentRecipient)
                .filter(
                    AssignmentRecipient.assignment_id == assignment.id,
                    AssignmentRecipient.learner_id == learner.id,
                )
                .first()
            )
            if recipient:
                reassessment = (
                    db.query(Reassessment)
                    .filter(Reassessment.assignment_recipient_id == recipient.id)
                    .first()
                )

        is_completed = recipient is not None and recipient.status == "completed"
        if is_completed:
            completed_count += 1

        reassessment_awarded = None
        reassessment_possible = None
        reassessment_percentage = None
        reassessment_items: List[ScoredResponseItem] = []

        if reassessment and reassessment.submission_state == "completed":
            responses = (
                db.query(ReassessmentResponse)
                .filter(ReassessmentResponse.reassessment_id == reassessment.id)
                .all()
            )
            awarded_sum = Decimal("0.0")
            possible_sum = Decimal("0.0")

            for resp in responses:
                q_item = fresh_items_map.get(resp.question_ref)
                max_m = Decimal(str(q_item.max_marks)) if q_item else Decimal("1.0")
                awarded_sum += Decimal(str(resp.awarded_marks))
                possible_sum += max_m

                reassessment_items.append(
                    ScoredResponseItem(
                        question_ref=resp.question_ref,
                        question_text=q_item.question_text if q_item else resp.question_ref,
                        expected_answer=q_item.expected_answer if q_item else "",
                        raw_response=resp.raw_response,
                        normalized_value=resp.normalized_value,
                        outcome=resp.outcome,
                        awarded_marks=float(resp.awarded_marks),
                        max_marks=float(max_m),
                        rationale=q_item.rationale if q_item else "",
                    )
                )

            reassessment_awarded = float(awarded_sum)
            reassessment_possible = float(possible_sum)
            reassessment_percentage = (
                round(float((awarded_sum / possible_sum) * 100), 2) if possible_sum > 0 else 0.0
            )

        learners_progress.append(
            LearnerProgressDetail(
                learner_id=learner.id,
                learner_ref=learner.external_ref,
                learner_name=f"{learner.first_name} {learner.last_name}",
                baseline_awarded=float(baseline_ev.awarded_marks) if baseline_ev else 0.0,
                baseline_possible=float(baseline_ev.possible_marks) if baseline_ev else 3.0,
                baseline_percentage=float(baseline_ev.percentage) if baseline_ev and baseline_ev.percentage is not None else 0.0,
                reassessment_awarded=reassessment_awarded,
                reassessment_possible=reassessment_possible,
                reassessment_percentage=reassessment_percentage,
                status=recipient.status if recipient else "unassigned",
                is_completed=is_completed,
                reassessment_items=reassessment_items,
            )
        )

    total_learners = len(group.members)
    return PlanProgressOut(
        plan_id=plan.id,
        plan_status=plan.status,
        support_group_id=group.id,
        support_group_name=group.name,
        topic_code=topic.code,
        topic_name=topic.name,
        assigned_version_num=version_num,
        total_learners=total_learners,
        completed_count=completed_count,
        all_completed=completed_count == total_learners,
        learners=learners_progress,
    )


@router.post("/plans/{plan_id}/close", response_model=PlanCloseOut)
def close_support_plan(
    plan_id: str,
    request: PlanCloseRequest,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Teacher action concluding or resetting the support cycle with mandatory observation rationale."""
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.id == plan_id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        raise ResourceNotFoundError("SupportPlan")

    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    ctx.assert_class_access(group.classroom_id)

    new_status = "closed" if request.action == "close" else "needs_revision"
    plan.status = new_status
    plan.revision += 1
    now = datetime.now(timezone.utc)
    plan.updated_at = now

    # Record decision on reassessments
    assignment = (
        db.query(Assignment)
        .filter(Assignment.plan_version_id == plan.current_version_id)
        .order_by(Assignment.created_at.desc())
        .first()
    )
    if assignment:
        for r in assignment.recipients:
            reassessment = (
                db.query(Reassessment)
                .filter(Reassessment.assignment_recipient_id == r.id)
                .first()
            )
            if reassessment:
                reassessment.teacher_decision = request.action
                reassessment.decision_rationale = request.rationale

    # Audit event
    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action=f"PLAN_{request.action.upper()}",
            entity_type="support_plan",
            entity_id=plan.id,
            metadata_json={
                "action": request.action,
                "rationale": request.rationale,
                "resulting_status": new_status,
            },
        )
    )

    db.commit()

    return PlanCloseOut(
        plan_id=plan.id,
        status=new_status,
        action_taken=request.action,
        rationale=request.rationale,
        decided_at=now,
    )
