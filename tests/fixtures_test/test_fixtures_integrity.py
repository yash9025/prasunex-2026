"""Fixture integrity and manifest alignment tests."""

import csv
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_baseline_csv_structure_and_counts():
    csv_path = FIXTURES_DIR / "synthetic_class6_baseline.csv"
    assert csv_path.exists(), "Baseline CSV fixture must exist."

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # 40 learners x 10 questions = 400 rows
    assert len(reader) == 400

    learners = {row["learner_ref"] for row in reader}
    assert len(learners) == 40

    questions = {row["question_ref"] for row in reader}
    assert len(questions) == 10


def test_primary_demo_learner_7_of_10():
    """Validates Aarav Patel (SYN-L6-014) exact scenario requirements."""
    csv_path = FIXTURES_DIR / "synthetic_class6_baseline.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    aarav_rows = {row["question_ref"]: row for row in reader if row["learner_ref"] == "SYN-L6-014"}
    assert len(aarav_rows) == 10

    # Fractions misconception: adds numerators & denominators
    assert aarav_rows["Q1"]["response"] == "2/5"  # Expected 5/6 -> Incorrect
    assert aarav_rows["Q2"]["response"] == "1/3"  # Expected 3/4 -> Incorrect
    assert aarav_rows["Q3"]["response"] == "2/5"  # Expected 2/5 -> Correct!

    # Decimals: 3/3 Correct
    assert aarav_rows["Q4"]["response"] == "0.75"
    assert aarav_rows["Q5"]["response"] == "0.8"
    assert aarav_rows["Q6"]["response"] == "0.4"

    # Percentages: 3/4 Correct
    assert aarav_rows["Q7"]["response"] == "40"
    assert aarav_rows["Q8"]["response"] == "1/4"
    assert aarav_rows["Q9"]["response"] == "15"
    assert aarav_rows["Q10"]["response"] == "0.7"  # Expected 0.75 -> Incorrect!


def test_expected_results_manifest_content():
    manifest_path = FIXTURES_DIR / "expected_results_manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    target_learners = manifest["target_learners"]
    assert "SYN-L6-014" in target_learners

    aarav = target_learners["SYN-L6-014"]
    assert aarav["overall"]["total_score"] == 7.0
    assert aarav["topics"]["MATH-G6-FRAC"]["awarded"] == 1.0
    assert aarav["topics"]["MATH-G6-FRAC"]["possible"] == 3.0
    assert aarav["topics"]["MATH-G6-FRAC"]["status"] == "pending_review"
