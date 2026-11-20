"""Unit tests for ExactAnswerChecker verifying safe rational arithmetic and equivalence."""

import pytest
from app.modules.scoring.checker import ExactAnswerChecker, OutcomeEnum


def test_fraction_exact_equivalence():
    # 5/6 equals 5/6
    res1 = ExactAnswerChecker.check_answer("5/6", "5/6", "numeric_fraction", 1.0)
    assert res1.outcome == OutcomeEnum.CORRECT
    assert res1.awarded_marks == 1.0

    # 10/12 equals 5/6 (unreduced equivalent fraction)
    res2 = ExactAnswerChecker.check_answer("10/12", "5/6", "numeric_fraction", 1.0)
    assert res2.outcome == OutcomeEnum.CORRECT
    assert res2.normalized_value == "5/6"

    # 2/4 equals 1/2
    res3 = ExactAnswerChecker.check_answer("2/4", "1/2", "numeric_fraction", 1.0)
    assert res3.outcome == OutcomeEnum.CORRECT
    assert res3.normalized_value == "1/2"

    # 2/5 does NOT equal 5/6
    res4 = ExactAnswerChecker.check_answer("2/5", "5/6", "numeric_fraction", 1.0)
    assert res4.outcome == OutcomeEnum.INCORRECT
    assert res4.awarded_marks == 0.0


def test_decimal_equivalence():
    # 0.75 equals 0.75
    res1 = ExactAnswerChecker.check_answer("0.75", "0.75", "numeric_decimal", 1.0)
    assert res1.outcome == OutcomeEnum.CORRECT

    # 0.750 equals 0.75
    res2 = ExactAnswerChecker.check_answer("0.750", "0.75", "numeric_decimal", 1.0)
    assert res2.outcome == OutcomeEnum.CORRECT

    # 0.8 equals 0.8
    res3 = ExactAnswerChecker.check_answer("0.8", "0.8", "numeric_decimal", 1.0)
    assert res3.outcome == OutcomeEnum.CORRECT

    # 0.7 does not equal 0.75
    res4 = ExactAnswerChecker.check_answer("0.7", "0.75", "numeric_decimal", 1.0)
    assert res4.outcome == OutcomeEnum.INCORRECT


def test_percentage_normalization():
    # 50% normalized to 1/2
    res1 = ExactAnswerChecker.check_answer("50%", "1/2", "numeric_percentage", 1.0)
    assert res1.outcome == OutcomeEnum.CORRECT

    # 25% normalized to 1/4
    res2 = ExactAnswerChecker.check_answer("25%", "1/4", "numeric_percentage", 1.0)
    assert res2.outcome == OutcomeEnum.CORRECT

    # 40 integer calculation
    res3 = ExactAnswerChecker.check_answer("40", "40", "numeric_integer", 1.0)
    assert res3.outcome == OutcomeEnum.CORRECT


def test_blanks_and_unattempted():
    res1 = ExactAnswerChecker.check_answer("", "5/6", "numeric_fraction", 1.0)
    assert res1.outcome == OutcomeEnum.UNATTEMPTED
    assert res1.awarded_marks == 0.0

    res2 = ExactAnswerChecker.check_answer("   ", "0.75", "numeric_decimal", 1.0)
    assert res2.outcome == OutcomeEnum.UNATTEMPTED


def test_invalid_syntax_and_division_by_zero():
    # 1/0 division by zero
    res1 = ExactAnswerChecker.check_answer("1/0", "5/6", "numeric_fraction", 1.0)
    assert res1.outcome == OutcomeEnum.INVALID

    # Code injection string
    res2 = ExactAnswerChecker.check_answer("import os; os.system('calc')", "5/6", "numeric_fraction", 1.0)
    assert res2.outcome == OutcomeEnum.INVALID

    # Malformed fraction
    res3 = ExactAnswerChecker.check_answer("1/2/3", "5/6", "numeric_fraction", 1.0)
    assert res3.outcome == OutcomeEnum.INVALID
