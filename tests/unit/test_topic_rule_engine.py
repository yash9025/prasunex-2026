"""Unit tests for TopicRuleEngine verifying diagnostic review heuristics and misconception detection."""

from decimal import Decimal
from app.modules.scoring.checker import ExactAnswerChecker, ScoringResult, OutcomeEnum
from app.modules.scoring.rules import AttemptRecord, TopicRuleEngine


def make_attempt(q_ref: str, text: str, exp: str, resp: str, max_m: float = 1.0) -> AttemptRecord:
    res = ExactAnswerChecker.check_answer(resp, exp, "numeric_fraction", max_m)
    return AttemptRecord(
        question_id=f"att-{q_ref}",
        question_ref=q_ref,
        topic_id="top-frac-001",
        topic_code="MATH-G6-FRAC",
        question_text=text,
        answer_kind="numeric_fraction",
        expected_answer=exp,
        raw_response=resp,
        scoring_result=res,
    )


def test_aarav_patel_fraction_misconception():
    """Aarav Patel profile: 1/3 correct on fractions (33.3%) with repeated misconception."""
    attempts = [
        make_attempt("Q1", "Evaluate 1/2 + 1/3", "5/6", "2/5"),  # Wrong: adds numerators & denominators
        make_attempt("Q2", "Evaluate 1/4 + 1/2", "3/4", "1/3"),  # Wrong: adds numerators & denominators
        make_attempt("Q3", "Evaluate 3/5 - 1/5", "2/5", "2/5"),  # Correct
    ]

    result = TopicRuleEngine.evaluate_topic("top-frac-001", "MATH-G6-FRAC", attempts)

    assert result.assessed_items_count == 3
    assert result.awarded_marks == Decimal("1.0")
    assert result.possible_marks == Decimal("3.0")
    assert result.percentage == Decimal("33.33")
    assert result.status == "pending_review"  # Below 60% threshold flagged
    assert result.suspected_pattern == "adds_numerators_and_denominators"


def test_boundary_score_exactly_60_percent():
    """At exactly 60%, the below-60 rule must NOT flag."""
    # 3 correct out of 5 items = 60.0%
    attempts = [
        make_attempt("Q1", "Q1 text", "1", "1"),
        make_attempt("Q2", "Q2 text", "1", "1"),
        make_attempt("Q3", "Q3 text", "1", "1"),
        make_attempt("Q4", "Q4 text", "1", "0"),
        make_attempt("Q5", "Q5 text", "1", "0"),
    ]

    result = TopicRuleEngine.evaluate_topic("top-test", "MATH-TEST", attempts)

    assert result.assessed_items_count == 5
    assert result.percentage == Decimal("60.00")
    assert result.status == "secure"  # 60.0% is not below 60.0%


def test_insufficient_evidence_under_three_items():
    """Fewer than 3 assessed items must trigger insufficient_evidence regardless of score."""
    attempts = [
        make_attempt("Q1", "Evaluate 1/2 + 1/3", "5/6", "2/5"),  # 0/1
        make_attempt("Q2", "Evaluate 1/4 + 1/2", "3/4", "1/3"),  # 0/2
    ]

    result = TopicRuleEngine.evaluate_topic("top-frac-001", "MATH-G6-FRAC", attempts)

    assert result.assessed_items_count == 2
    assert result.status == "insufficient_evidence"


def test_blanks_do_not_inflate_denominator_or_grant_security():
    """All blank responses must result in insufficient_evidence, not 0% or 100%."""
    attempts = [
        make_attempt("Q1", "Evaluate 1/2 + 1/3", "5/6", ""),
        make_attempt("Q2", "Evaluate 1/4 + 1/2", "3/4", ""),
        make_attempt("Q3", "Evaluate 3/5 - 1/5", "2/5", ""),
    ]

    result = TopicRuleEngine.evaluate_topic("top-frac-001", "MATH-G6-FRAC", attempts)

    assert result.assessed_items_count == 0
    assert result.unattempted_count == 3
    assert result.percentage is None
    assert result.status == "insufficient_evidence"
