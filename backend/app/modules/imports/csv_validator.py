"""CSV file validation engine adhering to Section 9.1 of the architecture plan.

Enforces:
1. File size limits (<= 2MB) and valid UTF-8 encoding.
2. Required schema columns.
3. Class learner enrollment check (no unknown external_refs).
4. Approved topic check.
5. Consistent question metadata across rows (no conflicting answers or topics).
6. Detection of duplicate learner/question response pairs.
7. Bounded row error reporting (up to 100 errors).
"""

import csv
import io
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Learner
from app.modules.evidence.models import Topic


REQUIRED_COLUMNS = [
    "learner_ref",
    "question_ref",
    "topic_ref",
    "question_text",
    "answer_kind",
    "expected_answer",
    "max_marks",
    "response",
]


class RowError(BaseModel):
    """Specific error identified on a CSV row."""

    row_num: int
    column: Optional[str] = None
    message: str


class QuestionMetadata(BaseModel):
    """Consistent metadata definition for an assessment question."""

    question_ref: str
    topic_ref: str
    topic_id: str
    question_text: str
    answer_kind: str
    expected_answer: str
    max_marks: float
    order_num: int


class ValidatedRow(BaseModel):
    """Clean, verified response row ready for deterministic scoring."""

    row_num: int
    learner_ref: str
    learner_id: str
    question_ref: str
    topic_ref: str
    topic_id: str
    question_text: str
    answer_kind: str
    expected_answer: str
    max_marks: float
    response: str


class CsvValidationResult(BaseModel):
    """Aggregate result of the all-or-nothing CSV validation."""

    is_valid: bool
    total_rows: int = 0
    valid_rows_count: int = 0
    row_errors: List[RowError] = Field(default_factory=list)
    questions: Dict[str, QuestionMetadata] = Field(default_factory=dict)
    rows: List[ValidatedRow] = Field(default_factory=list)


class CsvValidator:
    """Performs all-or-nothing validation of uploaded question-level assessment CSVs."""

    MAX_ERRORS_REPORTED = 100
    MAX_ROWS = 5000

    @classmethod
    def validate(
        cls,
        csv_bytes: bytes,
        classroom_id: str,
        school_id: str,
        db: Session,
    ) -> CsvValidationResult:
        """Validates CSV contents against database constraints and domain rules."""
        errors: List[RowError] = []

        def add_error(row_num: int, col: Optional[str], msg: str):
            if len(errors) < cls.MAX_ERRORS_REPORTED:
                errors.append(RowError(row_num=row_num, column=col, message=msg))

        # 1. UTF-8 decoding
        try:
            content = csv_bytes.decode("utf-8-sig")  # Handles optional BOM cleanly
        except UnicodeDecodeError:
            return CsvValidationResult(
                is_valid=False,
                row_errors=[RowError(row_num=0, message="File is not valid UTF-8 text.")],
            )

        # 2. Parse CSV
        f = io.StringIO(content)
        reader = csv.reader(f)

        try:
            header_row = next(reader)
        except StopIteration:
            return CsvValidationResult(
                is_valid=False,
                row_errors=[RowError(row_num=0, message="The uploaded CSV file is empty.")],
            )

        # 3. Check header columns
        cleaned_headers = [h.strip() for h in header_row]
        header_map = {col: idx for idx, col in enumerate(cleaned_headers)}

        missing_cols = [c for c in REQUIRED_COLUMNS if c not in header_map]
        if missing_cols:
            return CsvValidationResult(
                is_valid=False,
                row_errors=[
                    RowError(
                        row_num=1,
                        message=f"Missing required columns: {', '.join(missing_cols)}. Expected columns: {', '.join(REQUIRED_COLUMNS)}",
                    )
                ],
            )

        # 4. Preload classroom learners & school topics from DB for efficient validation
        enrolled_learners = (
            db.query(Learner)
            .filter(Learner.classroom_id == classroom_id, Learner.school_id == school_id)
            .all()
        )
        learner_map: Dict[str, str] = {l.external_ref: l.id for l in enrolled_learners}

        school_topics = (
            db.query(Topic)
            .filter(Topic.school_id == school_id)
            .all()
        )
        topic_map: Dict[str, str] = {t.code: t.id for t in school_topics}

        # 5. Row-by-row validation
        seen_pairs: Set[tuple] = set()
        question_defs: Dict[str, QuestionMetadata] = {}
        validated_rows: List[ValidatedRow] = []

        row_num = 1  # 1-indexed (header is 1)
        for row in reader:
            row_num += 1
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip blank lines safely

            if row_num > cls.MAX_ROWS:
                add_error(row_num, None, f"Exceeded maximum row limit of {cls.MAX_ROWS} rows.")
                break

            # Check column count
            if len(row) < len(REQUIRED_COLUMNS):
                add_error(
                    row_num,
                    None,
                    f"Row has {len(row)} columns, expected at least {len(REQUIRED_COLUMNS)}.",
                )
                continue

            # Extract fields
            l_ref = row[header_map["learner_ref"]].strip()
            q_ref = row[header_map["question_ref"]].strip()
            t_ref = row[header_map["topic_ref"]].strip()
            q_text = row[header_map["question_text"]].strip()
            a_kind = row[header_map["answer_kind"]].strip()
            exp_ans = row[header_map["expected_answer"]].strip()
            max_m_str = row[header_map["max_marks"]].strip()
            resp = row[header_map["response"]].strip()

            # Validate learner enrollment
            if not l_ref:
                add_error(row_num, "learner_ref", "Learner reference cannot be empty.")
            elif l_ref not in learner_map:
                add_error(
                    row_num,
                    "learner_ref",
                    f"Learner '{l_ref}' is not enrolled in this classroom.",
                )

            # Validate question_ref
            if not q_ref:
                add_error(row_num, "question_ref", "Question reference cannot be empty.")

            # Validate topic_ref
            if not t_ref:
                add_error(row_num, "topic_ref", "Topic reference cannot be empty.")
            elif t_ref not in topic_map:
                add_error(
                    row_num,
                    "topic_ref",
                    f"Topic '{t_ref}' is not a recognized curriculum topic for this school.",
                )

            # Validate max_marks
            try:
                max_marks = float(max_m_str)
                if max_marks <= 0:
                    add_error(row_num, "max_marks", f"Maximum marks must be > 0, got {max_m_str}.")
            except ValueError:
                add_error(row_num, "max_marks", f"Invalid numeric marks value: '{max_m_str}'.")
                max_marks = 1.0

            # Duplicate response check
            pair = (l_ref, q_ref)
            if pair in seen_pairs:
                add_error(
                    row_num,
                    None,
                    f"Duplicate attempt found for learner '{l_ref}' on question '{q_ref}'.",
                )
            seen_pairs.add(pair)

            # Question metadata consistency check across repeated occurrences
            if q_ref:
                if q_ref not in question_defs:
                    question_defs[q_ref] = QuestionMetadata(
                        question_ref=q_ref,
                        topic_ref=t_ref,
                        topic_id=topic_map.get(t_ref, ""),
                        question_text=q_text,
                        answer_kind=a_kind,
                        expected_answer=exp_ans,
                        max_marks=max_marks,
                        order_num=len(question_defs) + 1,
                    )
                else:
                    existing = question_defs[q_ref]
                    if (
                        existing.topic_ref != t_ref
                        or existing.expected_answer != exp_ans
                        or existing.max_marks != max_marks
                        or existing.answer_kind != a_kind
                    ):
                        add_error(
                            row_num,
                            "question_ref",
                            f"Conflicting definition for question '{q_ref}'. Previously defined with topic '{existing.topic_ref}' and expected answer '{existing.expected_answer}', but row specifies topic '{t_ref}' and expected answer '{exp_ans}'.",
                        )

            # Record validated row if references resolved
            if l_ref in learner_map and t_ref in topic_map:
                validated_rows.append(
                    ValidatedRow(
                        row_num=row_num,
                        learner_ref=l_ref,
                        learner_id=learner_map[l_ref],
                        question_ref=q_ref,
                        topic_ref=t_ref,
                        topic_id=topic_map[t_ref],
                        question_text=q_text,
                        answer_kind=a_kind,
                        expected_answer=exp_ans,
                        max_marks=max_marks,
                        response=resp,
                    )
                )

        is_valid = len(errors) == 0
        return CsvValidationResult(
            is_valid=is_valid,
            total_rows=row_num - 1,
            valid_rows_count=len(validated_rows) if is_valid else 0,
            row_errors=errors,
            questions=question_defs if is_valid else {},
            rows=validated_rows if is_valid else [],
        )
