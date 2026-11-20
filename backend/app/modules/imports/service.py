"""Import domain service managing transactional all-or-nothing CSV ingestion and deterministic scoring."""

from datetime import datetime, timezone
import hashlib
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.modules.audit.models import AuditEvent
from app.modules.evidence.models import (
    Assessment,
    Attempt,
    EvidenceAttempt,
    GapEvidence,
    Question,
    Topic,
)
from app.modules.imports.csv_validator import CsvValidator
from app.modules.imports.schemas import ImportUploadResponse, JobResultSummary
from app.modules.jobs.models import IdempotencyRecord, Job, OutboxEvent
from app.modules.scoring.checker import ExactAnswerChecker
from app.modules.scoring.rules import AttemptRecord, TopicRuleEngine


class ImportService:
    """Orchestrates CSV validation, exact arithmetic scoring, and topic evidence generation."""

    @classmethod
    def calculate_request_hash(cls, school_id: str, classroom_id: str, title: str, file_bytes: bytes) -> str:
        """Computes deterministic SHA-256 hash across parameters and raw payload."""
        h = hashlib.sha256()
        h.update(school_id.encode("utf-8"))
        h.update(classroom_id.encode("utf-8"))
        h.update(title.strip().encode("utf-8"))
        h.update(file_bytes)
        return h.hexdigest()

    @classmethod
    def submit_import(
        cls,
        file_bytes: bytes,
        classroom_id: str,
        assessment_title: str,
        actor_id: str,
        school_id: str,
        idempotency_key: Optional[str],
        db: Session,
    ) -> ImportUploadResponse:
        """Enforces idempotency, creates durable job record, and processes the import atomically."""
        request_hash = cls.calculate_request_hash(school_id, classroom_id, assessment_title, file_bytes)

        # 1. Check idempotency record if key provided
        if idempotency_key:
            existing_idemp = (
                db.query(IdempotencyRecord)
                .filter(
                    IdempotencyRecord.school_id == school_id,
                    IdempotencyRecord.actor_id == actor_id,
                    IdempotencyRecord.operation == "import_csv",
                    IdempotencyRecord.idempotency_key == idempotency_key,
                )
                .first()
            )
            if existing_idemp:
                if existing_idemp.request_hash == request_hash:
                    # Return original accepted response
                    saved = existing_idemp.response_body
                    return ImportUploadResponse(
                        job_id=saved["job_id"],
                        status=saved["status"],
                        message=saved["message"],
                        idempotency_key=idempotency_key,
                    )
                else:
                    # Reusing same key with different content
                    raise ConflictError(
                        "Idempotency-Key has already been reused for a different upload request."
                    )

        # 2. Create durable Job record (status: queued)
        job = Job(
            school_id=school_id,
            kind="csv_import",
            status="queued",
            request_hash=request_hash,
            attempt_count=1,
            max_attempts=3,
            heartbeat=datetime.now(timezone.utc),
        )
        db.add(job)
        db.flush()

        # 3. Create outbox event
        outbox = OutboxEvent(
            school_id=school_id,
            job_id=job.id,
            event_type="csv_import_queued",
            payload={"classroom_id": classroom_id, "title": assessment_title},
            status="dispatched",
        )
        db.add(outbox)

        # 4. Save initial idempotency record
        initial_response = {
            "job_id": job.id,
            "status": "queued",
            "message": "CSV assessment import has been accepted for processing.",
            "idempotency_key": idempotency_key,
        }
        if idempotency_key:
            db.add(
                IdempotencyRecord(
                    school_id=school_id,
                    actor_id=actor_id,
                    operation="import_csv",
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    status_code=202,
                    response_body=initial_response,
                )
            )
        db.commit()

        # 5. Process job synchronously for immediate reliability in API turn
        cls.execute_import_job(job.id, file_bytes, classroom_id, assessment_title, actor_id, school_id, db)

        # Refresh job state and update idempotency response
        db.refresh(job)
        final_msg = "CSV assessment import processed." if job.status == "succeeded" else f"Import failed: {job.failure_message}"
        final_response = {
            "job_id": job.id,
            "status": job.status,
            "message": final_msg,
            "idempotency_key": idempotency_key,
        }

        if idempotency_key:
            idemp_rec = db.query(IdempotencyRecord).filter(
                IdempotencyRecord.school_id == school_id,
                IdempotencyRecord.actor_id == actor_id,
                IdempotencyRecord.operation == "import_csv",
                IdempotencyRecord.idempotency_key == idempotency_key,
            ).first()
            if idemp_rec:
                idemp_rec.response_body = final_response
                db.commit()

        return ImportUploadResponse(
            job_id=job.id,
            status=job.status,
            message=final_msg,
            idempotency_key=idempotency_key,
        )

    @classmethod
    def execute_import_job(
        cls,
        job_id: str,
        file_bytes: bytes,
        classroom_id: str,
        assessment_title: str,
        actor_id: str,
        school_id: str,
        db: Session,
    ) -> None:
        """Executes full all-or-nothing validation, exact scoring, and evidence snapshotting."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.heartbeat = datetime.now(timezone.utc)
        db.commit()

        # Step A: Validate CSV
        val_result = CsvValidator.validate(file_bytes, classroom_id, school_id, db)
        if not val_result.is_valid:
            job.status = "failed"
            job.failure_code = "CSV_VALIDATION_FAILED"
            job.failure_message = f"CSV validation failed with {len(val_result.row_errors)} errors."
            job.result_summary = {
                "row_errors": [e.model_dump() for e in val_result.row_errors]
            }
            db.commit()
            return

        # Step B: All-or-nothing atomic database persistence
        try:
            # 1. Assessment
            assessment = (
                db.query(Assessment)
                .filter(
                    Assessment.classroom_id == classroom_id,
                    Assessment.title == assessment_title,
                    Assessment.school_id == school_id,
                )
                .first()
            )
            if not assessment:
                assessment = Assessment(
                    school_id=school_id,
                    classroom_id=classroom_id,
                    title=assessment_title,
                    academic_year="2026-2027",
                    status="imported",
                    revision=1,
                )
                db.add(assessment)
                db.flush()

            # 2. Questions
            question_model_map: Dict[str, Question] = {}
            for q_ref, q_meta in val_result.questions.items():
                q = (
                    db.query(Question)
                    .filter(
                        Question.assessment_id == assessment.id,
                        Question.question_ref == q_ref,
                    )
                    .first()
                )
                if not q:
                    q = Question(
                        school_id=school_id,
                        assessment_id=assessment.id,
                        topic_id=q_meta.topic_id,
                        question_ref=q_meta.question_ref,
                        question_text=q_meta.question_text,
                        answer_kind=q_meta.answer_kind,
                        expected_answer=q_meta.expected_answer,
                        max_marks=q_meta.max_marks,
                        order_num=q_meta.order_num,
                    )
                    db.add(q)
                    db.flush()
                question_model_map[q_ref] = q

            # 3. Score attempts and organize by (learner_id, topic_id)
            learner_topic_attempts: Dict[tuple, List[AttemptRecord]] = {}
            attempt_entities: List[Attempt] = []

            for row in val_result.rows:
                q_model = question_model_map[row.question_ref]
                scoring_res = ExactAnswerChecker.check_answer(
                    raw_response=row.response,
                    expected_answer=row.expected_answer,
                    answer_kind=row.answer_kind,
                    max_marks=row.max_marks,
                )

                # Upsert attempt
                att = (
                    db.query(Attempt)
                    .filter(
                        Attempt.learner_id == row.learner_id,
                        Attempt.question_id == q_model.id,
                        Attempt.assessment_id == assessment.id,
                    )
                    .first()
                )
                if not att:
                    att = Attempt(
                        school_id=school_id,
                        assessment_id=assessment.id,
                        learner_id=row.learner_id,
                        question_id=q_model.id,
                        raw_response=scoring_res.raw_response,
                        normalized_value=scoring_res.normalized_value,
                        outcome=scoring_res.outcome.value,
                        awarded_marks=scoring_res.awarded_marks,
                        scoring_version=scoring_res.scoring_version,
                    )
                    db.add(att)
                    db.flush()
                else:
                    att.raw_response = scoring_res.raw_response
                    att.normalized_value = scoring_res.normalized_value
                    att.outcome = scoring_res.outcome.value
                    att.awarded_marks = scoring_res.awarded_marks
                    att.scoring_version = scoring_res.scoring_version

                attempt_entities.append(att)

                pair_key = (row.learner_id, row.topic_id, row.topic_ref)
                if pair_key not in learner_topic_attempts:
                    learner_topic_attempts[pair_key] = []

                learner_topic_attempts[pair_key].append(
                    AttemptRecord(
                        question_id=att.id,
                        question_ref=row.question_ref,
                        topic_id=row.topic_id,
                        topic_code=row.topic_ref,
                        question_text=row.question_text,
                        answer_kind=row.answer_kind,
                        expected_answer=row.expected_answer,
                        raw_response=row.response,
                        scoring_result=scoring_res,
                    )
                )

            # 4. Evaluate Topic Rules and create GapEvidence snapshots
            pending_review_cnt = 0
            secure_cnt = 0
            insufficient_cnt = 0

            for (l_id, t_id, t_code), att_records in learner_topic_attempts.items():
                ev_result = TopicRuleEngine.evaluate_topic(
                    topic_id=t_id,
                    topic_code=t_code,
                    attempts=att_records,
                )

                if ev_result.status == "pending_review":
                    pending_review_cnt += 1
                elif ev_result.status == "secure":
                    secure_cnt += 1
                else:
                    insufficient_cnt += 1

                gap_ev = (
                    db.query(GapEvidence)
                    .filter(
                        GapEvidence.learner_id == l_id,
                        GapEvidence.assessment_id == assessment.id,
                        GapEvidence.topic_id == t_id,
                    )
                    .first()
                )
                if not gap_ev:
                    gap_ev = GapEvidence(
                        school_id=school_id,
                        assessment_id=assessment.id,
                        learner_id=l_id,
                        topic_id=t_id,
                        awarded_marks=ev_result.awarded_marks,
                        possible_marks=ev_result.possible_marks,
                        assessed_items_count=ev_result.assessed_items_count,
                        unattempted_count=ev_result.unattempted_count,
                        invalid_count=ev_result.invalid_count,
                        percentage=ev_result.percentage,
                        rule_version=ev_result.rule_version,
                        status=ev_result.status,
                    )
                    db.add(gap_ev)
                    db.flush()
                else:
                    gap_ev.awarded_marks = ev_result.awarded_marks
                    gap_ev.possible_marks = ev_result.possible_marks
                    gap_ev.assessed_items_count = ev_result.assessed_items_count
                    gap_ev.unattempted_count = ev_result.unattempted_count
                    gap_ev.invalid_count = ev_result.invalid_count
                    gap_ev.percentage = ev_result.percentage
                    gap_ev.status = ev_result.status

                # Evidence Attempt joins
                # Remove existing joins for idempotency
                db.query(EvidenceAttempt).filter(EvidenceAttempt.gap_evidence_id == gap_ev.id).delete()
                for rec in att_records:
                    db.add(
                        EvidenceAttempt(
                            gap_evidence_id=gap_ev.id,
                            attempt_id=rec.question_id,
                        )
                    )

            # 5. Audit Event
            db.add(
                AuditEvent(
                    school_id=school_id,
                    actor_id=actor_id,
                    action="ASSESSMENT_IMPORTED",
                    entity_type="assessment",
                    entity_id=assessment.id,
                    metadata_json={
                        "rows_processed": len(val_result.rows),
                        "questions_count": len(val_result.questions),
                        "pending_review_count": pending_review_cnt,
                    },
                )
            )

            # 6. Mark Job Succeeded
            distinct_learners = {r.learner_id for r in val_result.rows}
            distinct_topics = list({r.topic_ref for r in val_result.rows})

            summary = JobResultSummary(
                assessment_id=assessment.id,
                assessment_title=assessment.title,
                classroom_id=classroom_id,
                rows_processed=len(val_result.rows),
                questions_count=len(val_result.questions),
                learners_count=len(distinct_learners),
                topics_assessed=distinct_topics,
                pending_review_count=pending_review_cnt,
                secure_count=secure_cnt,
                insufficient_evidence_count=insufficient_cnt,
            )

            job.status = "succeeded"
            job.result_summary = summary.model_dump()
            db.commit()

        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.failure_code = "IMPORT_EXECUTION_ERROR"
            job.failure_message = f"An unexpected error occurred during database commit: {str(exc)}"
            db.commit()
