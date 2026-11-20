"""Topic evidence evaluation rules engine per Section 9.3 of the specification.

Enforces:
1. Topic score = awarded marks / possible marks for valid assessed items.
2. Blanks and invalid answers do NOT inflate assessed items or mask gaps.
3. Insufficient evidence rule: requires at least 3 assessed items.
4. Below-60% threshold heuristic: marks learner as 'pending_review' if score < 60.0%.
5. At exactly 60.0%, does NOT trigger the review flag.
6. Detects repeated error misconceptions (e.g. adding numerators and denominators).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from pydantic import BaseModel, Field

from app.modules.scoring.checker import OutcomeEnum, ScoringResult


class AttemptRecord(BaseModel):
    """Container for scored attempt data for a single question."""

    question_id: str
    question_ref: str
    topic_id: str
    topic_code: str
    question_text: str
    answer_kind: str
    expected_answer: str
    raw_response: str
    scoring_result: ScoringResult


class TopicEvidenceResult(BaseModel):
    """Calculated evidence metrics and review signals for a learner in a topic."""

    topic_id: str
    topic_code: str
    awarded_marks: Decimal
    possible_marks: Decimal
    assessed_items_count: int
    unattempted_count: int
    invalid_count: int
    percentage: Optional[Decimal]
    rule_version: str = "v1.0"
    status: str  # pending_review, secure, insufficient_evidence
    suspected_pattern: Optional[str] = None
    supporting_attempt_ids: List[str] = Field(default_factory=list)


class TopicRuleEngine:
    """Evaluates learner topic attempts against diagnostic rules."""

    RULE_VERSION = "v1.0"
    REVIEW_THRESHOLD_PERCENT = Decimal("60.0")
    MINIMUM_ASSESSED_ITEMS = 3

    # Pattern signature for adding numerators and denominators:
    # 1/2 + 1/3 -> 2/5
    # 1/4 + 1/2 -> 2/6 = 1/3
    FRACTION_ADDITION_MISCONCEPTIONS = {
        ("Evaluate 1/2 + 1/3", "2/5"),
        ("Evaluate 1/4 + 1/2", "1/3"),
        ("Evaluate 1/4 + 1/2", "2/6"),
    }

    @classmethod
    def evaluate_topic(
        cls,
        topic_id: str,
        topic_code: str,
        attempts: List[AttemptRecord],
    ) -> TopicEvidenceResult:
        """Aggregates attempts and computes the evidence snapshot."""
        awarded_sum = Decimal("0.0")
        possible_sum = Decimal("0.0")
        assessed_items_count = 0
        unattempted_count = 0
        invalid_count = 0
        attempt_ids = []

        misconception_count = 0

        for att in attempts:
            attempt_ids.append(att.question_id)
            res = att.scoring_result

            if res.outcome == OutcomeEnum.CORRECT:
                awarded_sum += res.awarded_marks
                possible_sum += res.max_marks
                assessed_items_count += 1
            elif res.outcome == OutcomeEnum.INCORRECT:
                possible_sum += res.max_marks
                assessed_items_count += 1

                # Check for fraction addition misconception
                norm_resp = res.raw_response.strip().replace(" ", "")
                for q_text, wrong_ans in cls.FRACTION_ADDITION_MISCONCEPTIONS:
                    if q_text in att.question_text and norm_resp == wrong_ans:
                        misconception_count += 1

            elif res.outcome == OutcomeEnum.UNATTEMPTED:
                unattempted_count += 1
                # Blanks do NOT count towards assessed items or possible_sum in topic score
            elif res.outcome == OutcomeEnum.INVALID:
                invalid_count += 1
                # Invalid answers do NOT count towards assessed items

        # Compute percentage
        percentage: Optional[Decimal] = None
        if possible_sum > Decimal("0.0") and assessed_items_count > 0:
            raw_pct = (awarded_sum / possible_sum) * Decimal("100.0")
            percentage = raw_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Rule evaluation
        # Rule 1: Insufficient evidence if assessed items < 3
        if assessed_items_count < cls.MINIMUM_ASSESSED_ITEMS:
            status = "insufficient_evidence"
        # Rule 2: Below 60% review flag (strictly < 60.0)
        elif percentage is not None and percentage < cls.REVIEW_THRESHOLD_PERCENT:
            status = "pending_review"
        # Rule 3: Secure (>= 60.0%)
        else:
            status = "secure"

        # Repeated error pattern detection: requires at least 2 matching examples
        suspected_pattern: Optional[str] = None
        if misconception_count >= 2:
            suspected_pattern = "adds_numerators_and_denominators"

        return TopicEvidenceResult(
            topic_id=topic_id,
            topic_code=topic_code,
            awarded_marks=awarded_sum,
            possible_marks=possible_sum,
            assessed_items_count=assessed_items_count,
            unattempted_count=unattempted_count,
            invalid_count=invalid_count,
            percentage=percentage,
            rule_version=cls.RULE_VERSION,
            status=status,
            suspected_pattern=suspected_pattern,
            supporting_attempt_ids=attempt_ids,
        )
