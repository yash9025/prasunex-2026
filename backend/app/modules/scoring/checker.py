"""Exact answer checking engine using exact rational arithmetic (fractions.Fraction).

Strictly avoids `eval` or unsafe code execution.
Guarantees mathematical equivalence for fractions (e.g. 5/6 == 10/12)
and decimals (e.g. 0.75 == 0.750).
"""

from decimal import Decimal, InvalidOperation
from enum import Enum
from fractions import Fraction
import re
from typing import Optional
from pydantic import BaseModel, Field


class OutcomeEnum(str, Enum):
    """Assessment item outcome classifications per Section 9.2."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNATTEMPTED = "unattempted"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires_review"


class ScoringResult(BaseModel):
    """Deterministic outcome of checking a student response."""

    outcome: OutcomeEnum
    awarded_marks: Decimal = Field(default=Decimal("0.0"))
    max_marks: Decimal = Field(default=Decimal("1.0"))
    normalized_value: Optional[str] = None
    raw_response: str
    scoring_version: str = "v1.0"
    rejection_reason: Optional[str] = None


class ExactAnswerChecker:
    """Safe, deterministic numeric response checker with exact rational equivalence."""

    CHECKER_VERSION = "v1.0"

    # Regex patterns for strict numerical input validation
    INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
    DECIMAL_PATTERN = re.compile(r"^[+-]?\d*\.\d+$")
    FRACTION_PATTERN = re.compile(r"^[+-]?\d+\s*/\s*[+-]?\d+$")
    PERCENTAGE_PATTERN = re.compile(r"^[+-]?\d+(\.\d+)?\s*%$")

    @classmethod
    def parse_to_fraction(cls, val_str: str) -> Optional[Fraction]:
        """Safely parses a validated string to an exact Fraction.

        Returns None if syntax is invalid or denominator is zero.
        """
        cleaned = val_str.strip()
        if not cleaned:
            return None

        # Check for division by zero or invalid characters
        if "/" in cleaned:
            parts = [p.strip() for p in cleaned.split("/")]
            if len(parts) != 2:
                return None
            try:
                num = int(parts[0])
                den = int(parts[1])
                if den == 0:
                    return None
                return Fraction(num, den)
            except (ValueError, OverflowError):
                return None

        # Check for percentage (e.g., 50% -> 50/100 -> 1/2)
        if cleaned.endswith("%"):
            pct_num = cleaned[:-1].strip()
            try:
                d = Decimal(pct_num)
                # Convert decimal percentage to fraction (e.g., 25% -> 25/100 -> 1/4)
                return Fraction(d) / Fraction(100)
            except (InvalidOperation, ValueError, OverflowError):
                return None

        # Standard decimal or integer
        try:
            d = Decimal(cleaned)
            return Fraction(d)
        except (InvalidOperation, ValueError, OverflowError):
            return None

    @classmethod
    def check_answer(
        cls,
        raw_response: Optional[str],
        expected_answer: str,
        answer_kind: str = "numeric_fraction",
        max_marks: float = 1.0,
    ) -> ScoringResult:
        """Determines correctness and awarded marks with rational equivalence.

        Handles blank answers as unattempted.
        Rejects invalid characters or division by zero as invalid.
        """
        marks_limit = Decimal(str(max_marks))

        # 1. Check for unattempted / blank response
        if raw_response is None or not raw_response.strip():
            return ScoringResult(
                outcome=OutcomeEnum.UNATTEMPTED,
                awarded_marks=Decimal("0.0"),
                max_marks=marks_limit,
                normalized_value=None,
                raw_response=raw_response or "",
                scoring_version=cls.CHECKER_VERSION,
                rejection_reason="Response is blank or unattempted",
            )

        cleaned_resp = raw_response.strip()

        # 2. Syntax sanitization: reject unexpected code, words, or complex operators
        # Allowed characters: digits, plus, minus, slash, dot, percent, space
        if not re.match(r"^[0-9+\-/.%\s]+$", cleaned_resp):
            return ScoringResult(
                outcome=OutcomeEnum.INVALID,
                awarded_marks=Decimal("0.0"),
                max_marks=marks_limit,
                normalized_value=None,
                raw_response=cleaned_resp,
                scoring_version=cls.CHECKER_VERSION,
                rejection_reason="Unsupported characters or expressions in numeric input",
            )

        # 3. Parse expected answer to exact Fraction
        expected_fraction = cls.parse_to_fraction(expected_answer)
        if expected_fraction is None:
            raise ValueError(f"Invalid question key specification: '{expected_answer}'")

        # 4. Parse student response to exact Fraction
        actual_fraction = cls.parse_to_fraction(cleaned_resp)
        if actual_fraction is None:
            return ScoringResult(
                outcome=OutcomeEnum.INVALID,
                awarded_marks=Decimal("0.0"),
                max_marks=marks_limit,
                normalized_value=None,
                raw_response=cleaned_resp,
                scoring_version=cls.CHECKER_VERSION,
                rejection_reason="Malformed numeric format or zero denominator",
            )

        normalized_str = (
            f"{actual_fraction.numerator}/{actual_fraction.denominator}"
            if actual_fraction.denominator != 1
            else str(actual_fraction.numerator)
        )

        # 5. Exact rational equivalence comparison
        if actual_fraction == expected_fraction:
            return ScoringResult(
                outcome=OutcomeEnum.CORRECT,
                awarded_marks=marks_limit,
                max_marks=marks_limit,
                normalized_value=normalized_str,
                raw_response=cleaned_resp,
                scoring_version=cls.CHECKER_VERSION,
            )
        else:
            return ScoringResult(
                outcome=OutcomeEnum.INCORRECT,
                awarded_marks=Decimal("0.0"),
                max_marks=marks_limit,
                normalized_value=normalized_str,
                raw_response=cleaned_resp,
                scoring_version=cls.CHECKER_VERSION,
                rejection_reason=f"Response {normalized_str} does not match expected key {expected_answer}",
            )
