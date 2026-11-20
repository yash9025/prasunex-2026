"""Demo Tenant Reset Engine adhering strictly to Specification Section 15.1.

Guarantees:
1. Targeted strictly to the designated synthetic demo tenant (Oakridge: sch-oakridge-001).
2. Environment-guarded (fails cleanly if APP_ENV == 'production_locked').
3. Preserves static tenant setup (School, Classrooms, Learners, Topics, Users, Snippets).
4. Atomically wipes dynamic transactions (assessments, attempts, evidence, groups, plans, assignments, quizzes, jobs).
5. Supports optional immediate baseline re-import for zero-latency presentation resets.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthorizationError, ValidationError
from app.modules.audit.models import AuditEvent
from app.modules.evidence.models import (
    Assessment,
    Question,
    Attempt,
    GapEvidence,
    EvidenceAttempt,
    TeacherDecision,
)
from app.modules.jobs.models import Job, IdempotencyRecord, OutboxEvent
from app.modules.plans.models import (
    SupportPlan,
    PlanVersion,
    PlanSource,
    Approval,
    SupportGroup,
    GroupMember,
    Assignment,
    AssignmentRecipient,
)
from app.modules.reassessments.models import Reassessment, ReassessmentResponse
from seeds.run_seed import OAKRIDGE_SCHOOL_ID, CLASS_6A_ID, TEACHER_PRIYA_ID


class DemoResetService:
    """Provides controlled, repeatable state reset for demonstrations and rehearsals."""

    @classmethod
    def reset_demo_tenant(
        cls,
        db: Session,
        school_id: str,
        actor_id: str,
        actor_name: str,
        preload_baseline: bool = False,
    ) -> Dict[str, Any]:
        """Atomically resets the demo school's dynamic transactions."""
        # 1. Environment Guard (Section 15.1)
        if getattr(settings, "APP_ENV", "") == "production_locked":
            raise AuthorizationError("Demo reset is permanently disabled in locked production environments.")

        # 2. Strict Tenant Guard (Only the synthetic demonstration school can be reset)
        if school_id != OAKRIDGE_SCHOOL_ID:
            raise AuthorizationError(
                f"Target school '{school_id}' is not an authorized synthetic demo tenant. Reset aborted."
            )

        # 3. Clean dynamic transaction tables for Oakridge
        # A. Reassessments
        reassessment_ids = [r.id for r in db.query(Reassessment.id).filter(Reassessment.school_id == school_id).all()]
        if reassessment_ids:
            db.query(ReassessmentResponse).filter(ReassessmentResponse.reassessment_id.in_(reassessment_ids)).delete(synchronize_session=False)
        db.query(Reassessment).filter(Reassessment.school_id == school_id).delete(synchronize_session=False)

        # B. Assignments & Recipients
        assignment_ids = [a.id for a in db.query(Assignment.id).filter(Assignment.school_id == school_id).all()]
        if assignment_ids:
            db.query(AssignmentRecipient).filter(AssignmentRecipient.assignment_id.in_(assignment_ids)).delete(synchronize_session=False)
        db.query(Assignment).filter(Assignment.school_id == school_id).delete(synchronize_session=False)

        # C. Support Plans, Versions & Cited Sources
        plan_ids = [p.id for p in db.query(SupportPlan.id).filter(SupportPlan.school_id == school_id).all()]
        if plan_ids:
            version_ids = [v.id for v in db.query(PlanVersion.id).filter(PlanVersion.support_plan_id.in_(plan_ids)).all()]
            if version_ids:
                db.query(PlanSource).filter(PlanSource.plan_version_id.in_(version_ids)).delete(synchronize_session=False)
                db.query(Approval).filter(Approval.plan_version_id.in_(version_ids)).delete(synchronize_session=False)
            db.query(PlanVersion).filter(PlanVersion.support_plan_id.in_(plan_ids)).delete(synchronize_session=False)
        db.query(SupportPlan).filter(SupportPlan.school_id == school_id).delete(synchronize_session=False)

        # D. Support Groups & Members
        group_ids = [g.id for g in db.query(SupportGroup.id).filter(SupportGroup.school_id == school_id).all()]
        if group_ids:
            db.query(GroupMember).filter(GroupMember.support_group_id.in_(group_ids)).delete(synchronize_session=False)
        db.query(SupportGroup).filter(SupportGroup.school_id == school_id).delete(synchronize_session=False)

        # E. Evidence & Evidence-Attempt linkages
        evidence_ids = [e.id for e in db.query(GapEvidence.id).filter(GapEvidence.school_id == school_id).all()]
        if evidence_ids:
            db.query(EvidenceAttempt).filter(EvidenceAttempt.gap_evidence_id.in_(evidence_ids)).delete(synchronize_session=False)
            db.query(TeacherDecision).filter(TeacherDecision.gap_evidence_id.in_(evidence_ids)).delete(synchronize_session=False)
        db.query(GapEvidence).filter(GapEvidence.school_id == school_id).delete(synchronize_session=False)

        # F. Assessment Attempts, Questions & Assessments
        db.query(Attempt).filter(Attempt.school_id == school_id).delete(synchronize_session=False)
        db.query(Question).filter(Question.school_id == school_id).delete(synchronize_session=False)
        db.query(Assessment).filter(Assessment.school_id == school_id).delete(synchronize_session=False)

        # G. Background Jobs & Idempotency Records
        db.query(OutboxEvent).filter(OutboxEvent.school_id == school_id).delete(synchronize_session=False)
        db.query(IdempotencyRecord).filter(IdempotencyRecord.school_id == school_id).delete(synchronize_session=False)
        db.query(Job).filter(Job.school_id == school_id).delete(synchronize_session=False)

        # H. Clear school-scoped audit logs (except recording the reset itself)
        db.query(AuditEvent).filter(AuditEvent.school_id == school_id).delete(synchronize_session=False)

        # 4. Record new tamper-evident audit event documenting the reset
        audit_reset_event = AuditEvent(
            school_id=school_id,
            actor_id=actor_id,
            action="demo_environment_reset",
            entity_type="school",
            entity_id=school_id,
            metadata_json={
                "actor_name": actor_name,
                "environment": settings.APP_ENV,
                "preload_baseline": preload_baseline,
                "reset_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_reset_event)
        db.commit()

        # 5. Optionally preload synthetic baseline dataset (Section 15.1)
        baseline_imported = False
        if preload_baseline:
            fixtures_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "fixtures" / "synthetic_class6_baseline.csv"
            if not fixtures_path.exists():
                fixtures_path = Path("fixtures/synthetic_class6_baseline.csv").resolve()

            if fixtures_path.exists():
                from app.modules.imports.service import ImportService
                csv_bytes = fixtures_path.read_bytes()
                import_res = ImportService.submit_import(
                    file_bytes=csv_bytes,
                    classroom_id=CLASS_6A_ID,
                    assessment_title="Class 6 Term 1 Diagnostic Baseline",
                    actor_id=actor_id,
                    school_id=school_id,
                    idempotency_key=f"demo-preload-{int(datetime.now(timezone.utc).timestamp())}",
                    db=db,
                )
                baseline_imported = True

        return {
            "status": "success",
            "message": "Demo environment reset successfully to clean starting state.",
            "school_id": school_id,
            "school_name": "Oakridge International Academy",
            "preloaded_baseline": baseline_imported,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
