"""Unit tests for deterministic mathematics verification and schema validation."""

import pytest
from fractions import Fraction
from app.modules.plans.drafting.context import DraftContext, SnippetContext
from app.modules.plans.drafting.verifier import (
    DraftContent,
    DraftValidator,
    MathSpec,
    MathVerifier,
    PracticeItem,
)


def test_math_verifier_exact_fraction_arithmetic():
    spec_add = MathSpec(operation="add", operands=["1/3", "1/6"], answer_format="fraction")
    res, err = MathVerifier.compute_exact(spec_add)
    assert err is None
    assert res == Fraction(1, 2)

    spec_sub = MathSpec(operation="subtract", operands=["3/4", "1/2"], answer_format="fraction")
    res, err = MathVerifier.compute_exact(spec_sub)
    assert err is None
    assert res == Fraction(1, 4)


def test_math_verifier_exact_decimal_arithmetic():
    spec_add = MathSpec(operation="add", operands=["0.75", "0.25"], answer_format="decimal")
    res, err = MathVerifier.compute_exact(spec_add)
    assert err is None
    assert res == Fraction(1, 1)  # 1.0

    spec_sub = MathSpec(operation="subtract", operands=["1.5", "0.25"], answer_format="decimal")
    res, err = MathVerifier.compute_exact(spec_sub)
    assert err is None
    assert res == Fraction(5, 4)  # 1.25


def test_math_verifier_percentage_arithmetic():
    spec = MathSpec(operation="add", operands=["50%", "25%"], answer_format="percentage")
    res, err = MathVerifier.compute_exact(spec)
    assert err is None
    assert res == Fraction(3, 4)  # 75%


def test_math_verifier_rejects_division_by_zero():
    spec = MathSpec(operation="divide", operands=["1/2", "0"], answer_format="fraction")
    res, err = MathVerifier.compute_exact(spec)
    assert res is None
    assert "Division by zero" in err


def test_practice_item_verification_success():
    item = PracticeItem(
        item_num=1,
        question_text="Calculate 1/3 + 1/6. Express your answer as a simplified fraction.",
        math_spec=MathSpec(operation="add", operands=["1/3", "1/6"], answer_format="fraction"),
        expected_answer="1/2",
        rationale="2/6 + 1/6 = 3/6 = 1/2.",
    )
    passed, err = MathVerifier.verify_item(item)
    assert passed is True
    assert err is None


def test_practice_item_verification_detects_miscalculated_answer():
    # Mistakenly says 1/3 + 1/6 = 2/9 (adding numerators and denominators)
    item = PracticeItem(
        item_num=1,
        question_text="Calculate 1/3 + 1/6. Express your answer as a simplified fraction.",
        math_spec=MathSpec(operation="add", operands=["1/3", "1/6"], answer_format="fraction"),
        expected_answer="2/9",
        rationale="Added numerators and denominators.",
    )
    passed, err = MathVerifier.verify_item(item)
    assert passed is False
    assert "mathematical mismatch" in err


def test_practice_item_verification_requires_operands_in_question():
    # Question text mentions 1/4 and 1/5, but spec uses 1/3 and 1/6
    item = PracticeItem(
        item_num=1,
        question_text="Calculate 1/4 + 1/5.",
        math_spec=MathSpec(operation="add", operands=["1/3", "1/6"], answer_format="fraction"),
        expected_answer="1/2",
        rationale="Find common denominator of 6.",
    )
    passed, err = MathVerifier.verify_item(item)
    assert passed is False
    assert "operand '1/3' is not mentioned" in err


def test_draft_validator_complete_valid_draft():
    context = DraftContext(
        topic_code="MATH-G6-FRAC",
        topic_name="Fractions",
        grade_level=6,
        language="en",
        snippets=[
            SnippetContext(
                id="snip-001",
                title="Common Denominators",
                content="Always find the common denominator.",
                source_ref="Oakridge Guide",
            )
        ],
    )
    draft = DraftContent(
        topic_code="MATH-G6-FRAC",
        source_ids=["snip-001"],
        explanation="Always convert fractions to like denominators before adding them.",
        practice_items=[
            PracticeItem(
                item_num=1,
                question_text="Calculate 1/3 + 1/6.",
                math_spec=MathSpec(operation="add", operands=["1/3", "1/6"]),
                expected_answer="1/2",
                rationale="Find common denominator 6: 2/6 + 1/6 = 3/6 = 1/2.",
            ),
            PracticeItem(
                item_num=2,
                question_text="Calculate 1/4 + 1/2.",
                math_spec=MathSpec(operation="add", operands=["1/4", "1/2"]),
                expected_answer="3/4",
                rationale="Convert 1/2 to 2/4: 1/4 + 2/4 = 3/4.",
            ),
            PracticeItem(
                item_num=3,
                question_text="Calculate 2/5 + 1/10.",
                math_spec=MathSpec(operation="add", operands=["2/5", "1/10"]),
                expected_answer="1/2",
                rationale="Convert 2/5 to 4/10: 4/10 + 1/10 = 5/10 = 1/2.",
            ),
        ],
    )
    report = DraftValidator.validate(draft, context)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_draft_validator_rejects_unapproved_source_and_wrong_topic():
    context = DraftContext(
        topic_code="MATH-G6-FRAC",
        topic_name="Fractions",
        snippets=[
            SnippetContext(
                id="snip-001",
                title="Common Denominators",
                content="Find LCM.",
                source_ref="Oakridge Guide",
            )
        ],
    )
    draft = DraftContent(
        topic_code="MATH-G6-DEC",  # Mismatched topic!
        source_ids=["unapproved-snip-999"],  # Unapproved source!
        explanation="Always convert fractions to like denominators before adding them.",
        practice_items=[
            PracticeItem(
                item_num=1,
                question_text="Calculate 1/3 + 1/6.",
                math_spec=MathSpec(operation="add", operands=["1/3", "1/6"]),
                expected_answer="1/2",
                rationale="Find common denominator 6: 2/6 + 1/6 = 3/6 = 1/2.",
            ),
            PracticeItem(
                item_num=2,
                question_text="Calculate 1/4 + 1/2.",
                math_spec=MathSpec(operation="add", operands=["1/4", "1/2"]),
                expected_answer="3/4",
                rationale="Convert 1/2 to 2/4: 1/4 + 2/4 = 3/4.",
            ),
            PracticeItem(
                item_num=3,
                question_text="Calculate 2/5 + 1/10.",
                math_spec=MathSpec(operation="add", operands=["2/5", "1/10"]),
                expected_answer="1/2",
                rationale="Convert 2/5 to 4/10: 4/10 + 1/10 = 5/10 = 1/2.",
            ),
        ],
    )
    report = DraftValidator.validate(draft, context)
    assert report.is_valid is False
    assert any("unapproved-snip-999" in err for err in report.errors)
    assert any("Topic code mismatch" in err for err in report.errors)
