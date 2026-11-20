"""Deterministic mathematics verification and schema validation for support drafting.

Per Section 11.2 of the specification:
1. Validates topic/source allowlists, item counts, and schema.
2. Recomputes practice item answers from structured mathematical specifications.
3. Rejects mismatches and unverified prose.
"""

from decimal import Decimal
from fractions import Fraction
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from app.modules.scoring.checker import ExactAnswerChecker, OutcomeEnum
from app.modules.plans.drafting.context import DraftContext


class MathSpec(BaseModel):
    """Structured mathematical specification required for all numeric practice items."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["add", "subtract", "multiply", "divide"]
    operands: List[str] = Field(..., min_length=2, max_length=2, description="Exactly two numeric operands")
    answer_format: Literal["fraction", "decimal", "percentage", "integer"] = "fraction"


class PracticeItem(BaseModel):
    """An individual practice item with deterministic mathematical grounding."""

    model_config = ConfigDict(extra="forbid")

    item_num: int = Field(..., ge=1, le=3)
    question_text: str = Field(..., min_length=10, max_length=500)
    math_spec: MathSpec
    expected_answer: str = Field(..., min_length=1, max_length=50)
    rationale: str = Field(..., min_length=10, max_length=1000)


class DraftContent(BaseModel):
    """Complete drafted intervention content."""

    model_config = ConfigDict(extra="forbid")

    topic_code: str
    source_ids: List[str] = Field(..., min_length=1)
    explanation: str = Field(..., min_length=30, max_length=3000)
    practice_items: List[PracticeItem] = Field(..., min_length=3, max_length=3)


class ValidationReport(BaseModel):
    """Result of validating draft structure and re-computing math specifications."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    item_verifications: List[dict] = Field(default_factory=list)


class MathVerifier:
    """Recomputes practice item solutions from structured specifications."""

    @classmethod
    def compute_exact(cls, spec: MathSpec) -> Tuple[Optional[Fraction], Optional[str]]:
        """Computes exact rational result from MathSpec operands and operation.
        
        Returns (result_fraction, error_message).
        """
        op1 = ExactAnswerChecker.parse_to_fraction(spec.operands[0])
        op2 = ExactAnswerChecker.parse_to_fraction(spec.operands[1])

        if op1 is None or op2 is None:
            return None, f"Invalid operand in {spec.operands}"

        try:
            if spec.operation == "add":
                res = op1 + op2
            elif spec.operation == "subtract":
                res = op1 - op2
            elif spec.operation == "multiply":
                res = op1 * op2
            elif spec.operation == "divide":
                if op2 == 0:
                    return None, "Division by zero in math specification"
                res = op1 / op2
            else:
                return None, f"Unsupported operation '{spec.operation}'"
            return res, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"

    @classmethod
    def verify_item(cls, item: PracticeItem) -> Tuple[bool, Optional[str]]:
        """Verifies an individual practice item against its mathematical specification.
        
        1. Checks that operands appear in question text.
        2. Recomputes exact fraction from operation and operands.
        3. Evaluates equivalence between item.expected_answer and computed fraction.
        """
        # 1. Operands consistency in question text
        for op in item.math_spec.operands:
            cleaned_op = op.replace(" ", "")
            cleaned_q = item.question_text.replace(" ", "")
            if cleaned_op not in cleaned_q:
                return False, f"Item {item.item_num}: operand '{op}' is not mentioned in question text."

        # 2. Recompute expected value
        computed_fraction, err = cls.compute_exact(item.math_spec)
        if err:
            return False, f"Item {item.item_num}: {err}"

        # 3. Verify equivalence of expected_answer against computed_fraction
        given_fraction = ExactAnswerChecker.parse_to_fraction(item.expected_answer)
        if given_fraction is None:
            return False, f"Item {item.item_num}: expected_answer '{item.expected_answer}' is not a valid numeric answer."

        if given_fraction != computed_fraction:
            return (
                False,
                f"Item {item.item_num}: mathematical mismatch. Computed {computed_fraction} from {item.math_spec.operation} on {item.math_spec.operands}, but expected_answer was '{item.expected_answer}' ({given_fraction}).",
            )

        return True, None


class DraftValidator:
    """Validates structural and mathematical invariants of a support draft."""

    @classmethod
    def validate(cls, draft: DraftContent, context: DraftContext) -> ValidationReport:
        errors: List[str] = []
        item_verifications: List[dict] = []

        # 1. Verify topic match
        if draft.topic_code != context.topic_code:
            errors.append(f"Topic code mismatch: draft has '{draft.topic_code}', context expects '{context.topic_code}'")

        # 2. Verify source allowlist
        allowed_source_ids = set(context.approved_snippet_ids)
        for s_id in draft.source_ids:
            if s_id not in allowed_source_ids:
                errors.append(f"Source ID '{s_id}' is not in the approved snippet context.")

        # 3. Verify item count and numbering
        if len(draft.practice_items) != 3:
            errors.append(f"Draft must contain exactly 3 practice items; found {len(draft.practice_items)}.")

        expected_nums = [1, 2, 3]
        actual_nums = [it.item_num for it in draft.practice_items]
        if actual_nums != expected_nums:
            errors.append(f"Practice item numbers must be sequentially [1, 2, 3]; found {actual_nums}.")

        # 4. Math verification of each item
        for item in draft.practice_items:
            passed, err_msg = MathVerifier.verify_item(item)
            item_verifications.append({
                "item_num": item.item_num,
                "verified": passed,
                "error": err_msg,
            })
            if not passed and err_msg:
                errors.append(err_msg)

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            item_verifications=item_verifications,
        )
