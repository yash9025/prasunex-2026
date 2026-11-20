"""Support group creation, grounded drafting, and immutable approval endpoints.

Implements Section 10 & Section 11 of the specification:
1. Support group management for confirmed learners.
2. Approved lesson snippets querying.
3. Provider-independent grounded support drafting with zero PII leakage.
4. Deterministic mathematical verification of numeric practice items.
5. Optimistic revision locking (409 Conflict) and immutable version freezing.
"""

from datetime import datetime, timezone
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
from app.modules.plans.drafting import (
    DraftCandidateCache,
    DraftContext,
    DraftValidator,
    MathSpec,
    MathVerifier,
    PracticeItem,
    SnippetContext,
    get_draft_provider,
)
from app.modules.plans.models import (
    Approval,
    ApprovedSnippet,
    GroupMember,
    PlanSource,
    PlanVersion,
    SupportGroup,
    SupportPlan,
)
from app.modules.plans.schemas import (
    ApprovalOut,
    ApprovedSnippetOut,
    DraftGenerationRequest,
    GroupMemberOut,
    PlanApprovalRequest,
    PlanDraftUpdate,
    PlanVersionOut,
    PracticeItemSchema,
    SupportGroupCreate,
    SupportGroupOut,
    SupportPlanOut,
)

router = APIRouter(prefix="", tags=["Support Groups & Grounded Drafting"])


# =========================================================================
# Support Group Endpoints (Section 10.3)
# =========================================================================


@router.post(
    "/groups",
    response_model=SupportGroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_support_group(
    request: SupportGroupCreate,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Creates a focused support group for learners with confirmed topic evidence."""
    ctx.assert_class_access(request.classroom_id)

    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == request.classroom_id, Classroom.school_id == ctx.school_id)
        .first()
    )
    if not classroom:
        raise ResourceNotFoundError("Classroom")

    topic = (
        db.query(Topic)
        .filter(Topic.id == request.topic_id, Topic.school_id == ctx.school_id)
        .first()
    )
    if not topic:
        raise ResourceNotFoundError("Topic")

    member_learner_ids = set()
    validated_members = []

    for m in request.members:
        if m.learner_id in member_learner_ids:
            raise ValidationError(f"Duplicate learner '{m.learner_id}' in group membership specification.")
        member_learner_ids.add(m.learner_id)

        learner = (
            db.query(Learner)
            .filter(
                Learner.id == m.learner_id,
                Learner.classroom_id == request.classroom_id,
                Learner.school_id == ctx.school_id,
            )
            .first()
        )
        if not learner:
            raise ValidationError(
                f"Learner '{m.learner_id}' does not belong to classroom '{request.classroom_id}' in this school."
            )

        evidence = (
            db.query(GapEvidence)
            .filter(
                GapEvidence.id == m.gap_evidence_id,
                GapEvidence.school_id == ctx.school_id,
                GapEvidence.learner_id == m.learner_id,
                GapEvidence.topic_id == request.topic_id,
            )
            .first()
        )
        if not evidence:
            raise ValidationError(
                f"Gap evidence '{m.gap_evidence_id}' does not exist for learner '{learner.external_ref}' on topic '{topic.code}'."
            )

        if evidence.status != "confirmed":
            raise ValidationError(
                f"Cannot create support group with unconfirmed evidence for learner '{learner.external_ref}'. Status is '{evidence.status}', must be 'confirmed'."
            )

        validated_members.append((learner, evidence))

    group = SupportGroup(
        school_id=ctx.school_id,
        classroom_id=request.classroom_id,
        topic_id=request.topic_id,
        name=request.name.strip(),
        created_by_id=ctx.user_id,
    )
    db.add(group)
    db.flush()

    members_out: List[GroupMemberOut] = []
    for learner, ev in validated_members:
        gm = GroupMember(
            support_group_id=group.id,
            learner_id=learner.id,
            gap_evidence_id=ev.id,
        )
        db.add(gm)
        db.flush()

        members_out.append(
            GroupMemberOut(
                id=gm.id,
                learner_id=learner.id,
                learner_ref=learner.external_ref,
                learner_name=f"{learner.first_name} {learner.last_name}",
                gap_evidence_id=ev.id,
            )
        )

    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="SUPPORT_GROUP_CREATED",
            entity_type="support_group",
            entity_id=group.id,
            metadata_json={
                "classroom_id": request.classroom_id,
                "topic_id": request.topic_id,
                "member_count": len(members_out),
            },
        )
    )

    db.commit()

    return SupportGroupOut(
        id=group.id,
        school_id=ctx.school_id,
        classroom_id=classroom.id,
        topic_id=topic.id,
        topic_code=topic.code,
        topic_name=topic.name,
        name=group.name,
        created_by_id=ctx.user_id,
        created_by_name=ctx.full_name,
        members=members_out,
        created_at=group.created_at,
    )


@router.get("/classes/{classroom_id}/groups", response_model=List[SupportGroupOut])
def list_support_groups(
    classroom_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns all support groups formed for an authorized classroom."""
    ctx.assert_class_access(classroom_id)

    groups = (
        db.query(SupportGroup, Topic, User)
        .join(Topic, SupportGroup.topic_id == Topic.id)
        .join(User, SupportGroup.created_by_id == User.id)
        .filter(
            SupportGroup.classroom_id == classroom_id,
            SupportGroup.school_id == ctx.school_id,
        )
        .order_by(SupportGroup.created_at.desc())
        .all()
    )

    result: List[SupportGroupOut] = []
    for grp, top, usr in groups:
        gms = (
            db.query(GroupMember, Learner)
            .join(Learner, GroupMember.learner_id == Learner.id)
            .filter(GroupMember.support_group_id == grp.id)
            .order_by(Learner.external_ref.asc())
            .all()
        )

        members_out = [
            GroupMemberOut(
                id=gm.GroupMember.id,
                learner_id=gm.Learner.id,
                learner_ref=gm.Learner.external_ref,
                learner_name=f"{gm.Learner.first_name} {gm.Learner.last_name}",
                gap_evidence_id=gm.GroupMember.gap_evidence_id,
            )
            for gm in gms
        ]

        result.append(
            SupportGroupOut(
                id=grp.id,
                school_id=grp.school_id,
                classroom_id=grp.classroom_id,
                topic_id=top.id,
                topic_code=top.code,
                topic_name=top.name,
                name=grp.name,
                created_by_id=usr.id,
                created_by_name=usr.full_name,
                members=members_out,
                created_at=grp.created_at,
            )
        )

    return result


@router.get("/groups/{group_id}/plan", response_model=Optional[SupportPlanOut])
def get_group_plan(
    group_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves the active intervention plan for a support group if one exists."""
    group = (
        db.query(SupportGroup)
        .filter(SupportGroup.id == group_id, SupportGroup.school_id == ctx.school_id)
        .first()
    )
    if not group:
        raise ResourceNotFoundError("SupportGroup")
    ctx.assert_class_access(group.classroom_id)
    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()

    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.support_group_id == group.id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        return None
    return _build_plan_out(plan, group, topic, db)


# =========================================================================
# Phase 4: Approved Snippet Library Endpoints (Section 11.1)
# =========================================================================


@router.get("/snippets", response_model=List[ApprovedSnippetOut])
def list_approved_snippets(
    topic_id: Optional[str] = Query(None, description="Optional curriculum topic filter"),
    grade_level: Optional[int] = Query(6, description="Grade level filter"),
    language: Optional[str] = Query("en", description="Language filter"),
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves teacher-approved lesson snippets scoped to the tenant school."""
    query = db.query(ApprovedSnippet).filter(
        ApprovedSnippet.school_id == ctx.school_id,
        ApprovedSnippet.is_approved == True,
    )
    if topic_id:
        query = query.filter(ApprovedSnippet.topic_id == topic_id)
    if grade_level:
        query = query.filter(ApprovedSnippet.grade_level == grade_level)
    if language:
        query = query.filter(ApprovedSnippet.language == language)

    snippets = query.order_by(ApprovedSnippet.created_at.asc()).all()
    return snippets


# =========================================================================
# Phase 4: Grounded Support Drafting Endpoints (Section 11.2 - 11.4)
# =========================================================================


def _build_plan_out(plan: SupportPlan, group: SupportGroup, topic: Topic, db: Session) -> SupportPlanOut:
    """Helper to assemble a SupportPlanOut model with nested PlanVersion and citations."""
    current_ver = None
    if plan.current_version_id:
        pv, creator = (
            db.query(PlanVersion, User)
            .join(User, PlanVersion.created_by_id == User.id)
            .filter(PlanVersion.id == plan.current_version_id)
            .first()
        )
        if pv:
            # Query cited snippets
            sources = (
                db.query(ApprovedSnippet)
                .join(PlanSource, PlanSource.snippet_id == ApprovedSnippet.id)
                .filter(PlanSource.plan_version_id == pv.id)
                .all()
            )
            current_ver = PlanVersionOut(
                id=pv.id,
                support_plan_id=plan.id,
                version_num=pv.version_num,
                explanation=pv.explanation,
                practice_items=pv.practice_items,
                content_hash=pv.content_hash,
                cited_snippets=sources,
                created_by_id=creator.id,
                created_by_name=creator.full_name,
                created_at=pv.created_at,
            )

    return SupportPlanOut(
        id=plan.id,
        school_id=plan.school_id,
        support_group_id=group.id,
        support_group_name=group.name,
        topic_id=topic.id,
        topic_code=topic.code,
        topic_name=topic.name,
        status=plan.status,
        revision=plan.revision,
        current_version_id=plan.current_version_id,
        current_version=current_ver,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post(
    "/plans/drafts",
    response_model=SupportPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def generate_support_draft(
    request: DraftGenerationRequest,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Generates a grounded intervention draft for a support group.
    
    Guarantees:
    1. Zero learner PII sent to draft providers.
    2. Selected sources must be teacher-approved and belong to the active school & topic.
    3. Exactly 3 practice items mathematically verified against structured specifications.
    4. Immutable PlanVersion record created with SHA-256 content hash.
    """
    # 1. Authorize Support Group
    group = (
        db.query(SupportGroup)
        .filter(SupportGroup.id == request.support_group_id, SupportGroup.school_id == ctx.school_id)
        .first()
    )
    if not group:
        raise ResourceNotFoundError("SupportGroup")
    ctx.assert_class_access(group.classroom_id)

    topic = db.query(Topic).filter(Topic.id == group.topic_id).first()
    if not topic:
        raise ResourceNotFoundError("Topic")

    # 2. Retrieve & Verify Approved Snippets
    snippets = (
        db.query(ApprovedSnippet)
        .filter(
            ApprovedSnippet.id.in_(request.source_snippet_ids),
            ApprovedSnippet.school_id == ctx.school_id,
            ApprovedSnippet.topic_id == topic.id,
            ApprovedSnippet.is_approved == True,
        )
        .all()
    )
    if len(snippets) != len(request.source_snippet_ids):
        raise ValidationError(
            "One or more requested snippets are invalid, unapproved, belong to another school, or do not match the group topic."
        )

    # 3. Build strictly PII-safe DraftContext
    snippet_contexts = [
        SnippetContext(
            id=s.id,
            title=s.title,
            content=s.content,
            source_ref=s.source_ref,
        )
        for s in snippets
    ]
    context = DraftContext(
        topic_code=topic.code,
        topic_name=topic.name,
        grade_level=snippets[0].grade_level,
        language=snippets[0].language,
        snippets=snippet_contexts,
    )

    # 4. Invoke Provider (AI or deterministic template fallback)
    provider = get_draft_provider(request.generation_mode)
    gen_result = provider.generate(context)

    # 5. Validate draft structure and mathematical specifications
    report = DraftValidator.validate(gen_result.draft, context)
    if not report.is_valid:
        raise ValidationError(
            f"Draft content failed mathematical verification: {'; '.join(report.errors)}"
        )

    # 6. Locate or initialize SupportPlan
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.support_group_id == group.id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        plan = SupportPlan(
            school_id=ctx.school_id,
            support_group_id=group.id,
            status="draft",
            revision=1,
        )
        db.add(plan)
        db.flush()

    # Determine version number
    version_count = (
        db.query(PlanVersion)
        .filter(PlanVersion.support_plan_id == plan.id)
        .count()
    )
    next_version_num = version_count + 1

    # Format practice items for storage with verification metadata
    stored_items = []
    for it in gen_result.draft.practice_items:
        stored_items.append({
            "item_num": it.item_num,
            "question_text": it.question_text,
            "math_spec": it.math_spec.model_dump(),
            "expected_answer": it.expected_answer,
            "rationale": it.rationale,
            "verified": True,
            "verification_error": None,
        })

    # Compute content hash
    content_payload = {
        "explanation": gen_result.draft.explanation,
        "practice_items": stored_items,
        "source_ids": sorted(gen_result.draft.source_ids),
    }
    content_hash = hashlib.sha256(json.dumps(content_payload, sort_keys=True).encode("utf-8")).hexdigest()

    # Create immutable PlanVersion
    plan_version = PlanVersion(
        support_plan_id=plan.id,
        version_num=next_version_num,
        explanation=gen_result.draft.explanation,
        practice_items=stored_items,
        content_hash=content_hash,
        created_by_id=ctx.user_id,
    )
    db.add(plan_version)
    db.flush()

    # Link PlanSources
    for s_id in gen_result.draft.source_ids:
        ps = PlanSource(
            plan_version_id=plan_version.id,
            snippet_id=s_id,
            citation_note=f"Grounded source citation for Topic {topic.code}",
        )
        db.add(ps)

    # Update SupportPlan
    plan.current_version_id = plan_version.id
    plan.status = "draft"
    plan.revision += 1

    # Log Audit Event
    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="DRAFT_CREATED",
            entity_type="support_plan",
            entity_id=plan.id,
            metadata_json={
                "version_id": plan_version.id,
                "version_num": next_version_num,
                "generation_mode": gen_result.generation_mode,
                "provider": gen_result.provider_name,
                "is_fallback": gen_result.is_fallback,
                "content_hash": content_hash,
            },
        )
    )

    db.commit()

    res = _build_plan_out(plan, group, topic, db)
    res.generation_mode = gen_result.generation_mode
    res.is_fallback = gen_result.is_fallback
    res.fallback_reason = gen_result.fallback_reason
    return res


@router.get("/plans/{plan_id}", response_model=SupportPlanOut)
def get_support_plan(
    plan_id: str,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves full intervention plan details with active version and citations."""
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

    return _build_plan_out(plan, group, topic, db)


@router.patch("/plans/{plan_id}/draft", response_model=SupportPlanOut)
def update_support_draft(
    plan_id: str,
    request: PlanDraftUpdate,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Applies teacher edits to draft explanation or practice items.
    
    Enforces:
    1. Optimistic revision check (returns 409 Conflict if plan was modified).
    2. Re-runs mathematical verification on modified numeric practice items.
    3. Freezes edit into a new PlanVersion incrementing version_num.
    """
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

    # Optimistic locking
    if plan.revision != request.revision:
        raise ConflictError(
            f"Plan revision conflict. Expected revision {plan.revision}, but received {request.revision}. Please refresh."
        )

    if plan.status in ["assigned", "closed"]:
        raise ValidationError(f"Cannot edit plan in '{plan.status}' status. Create a new revision instead.")

    # Load current version
    current_ver = (
        db.query(PlanVersion)
        .filter(PlanVersion.id == plan.current_version_id)
        .first()
    )
    if not current_ver:
        raise ValidationError("Cannot update draft: no active draft version exists.")

    explanation = request.explanation if request.explanation is not None else current_ver.explanation

    # Validate practice items if updated
    if request.practice_items is not None:
        if len(request.practice_items) != 3:
            raise ValidationError(f"Intervention must have exactly 3 practice items; received {len(request.practice_items)}.")

        stored_items = []
        for idx, it in enumerate(request.practice_items):
            pi = PracticeItem(
                item_num=it.item_num,
                question_text=it.question_text,
                math_spec=MathSpec(**it.math_spec.model_dump()),
                expected_answer=it.expected_answer,
                rationale=it.rationale,
            )
            passed, err = MathVerifier.verify_item(pi)
            if not passed:
                raise ValidationError(f"Math verification failed on item {pi.item_num}: {err}")

            stored_items.append({
                "item_num": pi.item_num,
                "question_text": pi.question_text,
                "math_spec": pi.math_spec.model_dump(),
                "expected_answer": pi.expected_answer,
                "rationale": pi.rationale,
                "verified": True,
                "verification_error": None,
            })
    else:
        stored_items = current_ver.practice_items

    # Compute new content hash
    content_payload = {
        "explanation": explanation,
        "practice_items": stored_items,
    }
    new_hash = hashlib.sha256(json.dumps(content_payload, sort_keys=True).encode("utf-8")).hexdigest()

    # Create new PlanVersion
    new_ver_num = current_ver.version_num + 1
    new_version = PlanVersion(
        support_plan_id=plan.id,
        version_num=new_ver_num,
        explanation=explanation,
        practice_items=stored_items,
        content_hash=new_hash,
        created_by_id=ctx.user_id,
    )
    db.add(new_version)
    db.flush()

    # Copy sources from current version
    existing_sources = (
        db.query(PlanSource)
        .filter(PlanSource.plan_version_id == current_ver.id)
        .all()
    )
    for es in existing_sources:
        db.add(PlanSource(
            plan_version_id=new_version.id,
            snippet_id=es.snippet_id,
            citation_note=es.citation_note,
        ))

    # Update plan
    plan.current_version_id = new_version.id
    plan.revision += 1
    plan.updated_at = datetime.now(timezone.utc)

    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="DRAFT_UPDATED",
            entity_type="support_plan",
            entity_id=plan.id,
            metadata_json={
                "previous_version_id": current_ver.id,
                "new_version_id": new_version.id,
                "new_version_num": new_ver_num,
                "content_hash": new_hash,
            },
        )
    )

    db.commit()
    return _build_plan_out(plan, group, topic, db)


@router.post("/plans/{plan_id}/approve", response_model=ApprovalOut)
def approve_support_plan(
    plan_id: str,
    request: PlanApprovalRequest,
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Explicit teacher sign-off freezing a plan version for assignment.
    
    Enforces:
    1. Teacher must explicitly accept instructional responsibility.
    2. Optimistic locking on plan.revision (returns 409 Conflict if modified).
    3. Immutable Approval record created with cryptographic hash.
    4. Plan status transitions to 'reviewed'.
    """
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.id == plan_id, SupportPlan.school_id == ctx.school_id)
        .first()
    )
    if not plan:
        raise ResourceNotFoundError("SupportPlan")

    group = db.query(SupportGroup).filter(SupportGroup.id == plan.support_group_id).first()
    ctx.assert_class_access(group.classroom_id)

    if not request.sign_off_responsibility:
        raise ValidationError("Teacher sign-off is required: teacher must accept pedagogical responsibility.")

    if plan.revision != request.revision:
        raise ConflictError(
            f"Plan revision conflict. Expected revision {plan.revision}, but received {request.revision}. Please refresh."
        )

    current_ver = (
        db.query(PlanVersion)
        .filter(PlanVersion.id == plan.current_version_id)
        .first()
    )
    if not current_ver:
        raise ValidationError("Cannot approve: plan has no active version.")

    # Cryptographic approval hash
    approval_timestamp = datetime.now(timezone.utc)
    raw_hash_material = f"{current_ver.content_hash}:{ctx.user_id}:{approval_timestamp.isoformat()}"
    approval_hash = hashlib.sha256(raw_hash_material.encode("utf-8")).hexdigest()

    approval = Approval(
        plan_version_id=current_ver.id,
        approver_id=ctx.user_id,
        approval_hash=approval_hash,
        approved_at=approval_timestamp,
    )
    db.add(approval)

    plan.status = "reviewed"
    plan.revision += 1
    plan.updated_at = approval_timestamp

    db.add(
        AuditEvent(
            school_id=ctx.school_id,
            actor_id=ctx.user_id,
            action="PLAN_APPROVED",
            entity_type="support_plan",
            entity_id=plan.id,
            metadata_json={
                "version_id": current_ver.id,
                "version_num": current_ver.version_num,
                "approval_hash": approval_hash,
            },
        )
    )

    db.commit()

    return ApprovalOut(
        id=approval.id,
        plan_version_id=current_ver.id,
        approver_id=ctx.user_id,
        approver_name=ctx.full_name,
        approval_hash=approval_hash,
        approved_at=approval_timestamp,
    )
