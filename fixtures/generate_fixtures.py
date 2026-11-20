"""Generates deterministic synthetic fixtures and expected-results manifest.

Outputs:
1. synthetic_class6_baseline.csv: 40 learners x 10 questions = 400 responses.
2. synthetic_class6_malformed_headers.csv: corrupt headers for validation test.
3. synthetic_class6_mismatched_metadata.csv: conflicting question definitions.
4. synthetic_class6_boundary_cases.csv: equivalent fractions/decimals, blank responses, boundary 60%.
5. synthetic_low_evidence.csv: 2-question assessment for insufficient evidence rule.
6. expected_results_manifest.json: independently verified expected scores and flags.
"""

import csv
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent

QUESTIONS = [
    {
        "ref": "Q1",
        "topic": "MATH-G6-FRAC",
        "text": "Evaluate 1/2 + 1/3",
        "kind": "numeric_fraction",
        "expected": "5/6",
        "marks": "1.0",
    },
    {
        "ref": "Q2",
        "topic": "MATH-G6-FRAC",
        "text": "Evaluate 1/4 + 1/2",
        "kind": "numeric_fraction",
        "expected": "3/4",
        "marks": "1.0",
    },
    {
        "ref": "Q3",
        "topic": "MATH-G6-FRAC",
        "text": "Evaluate 3/5 - 1/5",
        "kind": "numeric_fraction",
        "expected": "2/5",
        "marks": "1.0",
    },
    {
        "ref": "Q4",
        "topic": "MATH-G6-DEC",
        "text": "Calculate 0.25 + 0.5",
        "kind": "numeric_decimal",
        "expected": "0.75",
        "marks": "1.0",
    },
    {
        "ref": "Q5",
        "topic": "MATH-G6-DEC",
        "text": "Calculate 1.5 - 0.7",
        "kind": "numeric_decimal",
        "expected": "0.8",
        "marks": "1.0",
    },
    {
        "ref": "Q6",
        "topic": "MATH-G6-DEC",
        "text": "Calculate 0.1 * 4",
        "kind": "numeric_decimal",
        "expected": "0.4",
        "marks": "1.0",
    },
    {
        "ref": "Q7",
        "topic": "MATH-G6-PCT",
        "text": "Calculate 50% of 80",
        "kind": "numeric_integer",
        "expected": "40",
        "marks": "1.0",
    },
    {
        "ref": "Q8",
        "topic": "MATH-G6-PCT",
        "text": "Convert 25% to a simplified fraction",
        "kind": "numeric_fraction",
        "expected": "1/4",
        "marks": "1.0",
    },
    {
        "ref": "Q9",
        "topic": "MATH-G6-PCT",
        "text": "Calculate 10% of 150",
        "kind": "numeric_integer",
        "expected": "15",
        "marks": "1.0",
    },
    {
        "ref": "Q10",
        "topic": "MATH-G6-PCT",
        "text": "Convert 75% to a decimal",
        "kind": "numeric_decimal",
        "expected": "0.75",
        "marks": "1.0",
    },
]


def generate_baseline_csv() -> None:
    """Generates the primary 40-learner baseline CSV."""
    filepath = FIXTURES_DIR / "synthetic_class6_baseline.csv"
    rows = []

    # Fieldnames matching Section 9.1
    fieldnames = [
        "learner_ref",
        "question_ref",
        "topic_ref",
        "question_text",
        "answer_kind",
        "expected_answer",
        "max_marks",
        "response",
    ]

    for i in range(1, 41):
        ref = f"SYN-L6-{i:03d}"

        for q in QUESTIONS:
            q_ref = q["ref"]

            # 1. Primary Demo Learner: SYN-L6-014 (Aarav Patel)
            # Scores 7/10 overall, 1/3 in fractions (33.3% -> below 60% threshold)
            if ref == "SYN-L6-014":
                if q_ref == "Q1":
                    resp = "2/5"  # Misconception: (1+1)/(2+3) = 2/5 (Incorrect)
                elif q_ref == "Q2":
                    resp = "1/3"  # Misconception: (1+1)/(4+2) = 2/6 = 1/3 (Incorrect)
                elif q_ref == "Q3":
                    resp = "2/5"  # Correct (3/5 - 1/5 = 2/5)
                elif q_ref in ("Q4", "Q5", "Q6"):
                    resp = q["expected"]  # 3/3 in Decimals (Correct)
                elif q_ref in ("Q7", "Q8", "Q9"):
                    resp = q["expected"]  # Correct in Percentages
                elif q_ref == "Q10":
                    resp = "0.7"  # Wrong (expected 0.75) -> 3/4 in Percentages. Total = 1+3+3 = 7/10!

            # 2. Similar Misconception Partner: SYN-L6-015 (Diya Sen)
            elif ref == "SYN-L6-015":
                if q_ref == "Q1":
                    resp = "2/5"  # Incorrect
                elif q_ref == "Q2":
                    resp = "1/3"  # Incorrect
                elif q_ref == "Q3":
                    resp = "2/5"  # Correct
                elif q_ref in ("Q4", "Q5"):
                    resp = q["expected"]
                elif q_ref == "Q6":
                    resp = "0.5"  # Incorrect
                elif q_ref in ("Q7", "Q8", "Q9"):
                    resp = q["expected"]
                else:
                    resp = "0.7"  # Incorrect -> 1/3 Frac, 2/3 Dec, 3/4 Pct = 6/10

            # 3. Low performer in fractions: SYN-L6-016 (Kabir Nair)
            elif ref == "SYN-L6-016":
                if q_ref in ("Q1", "Q2", "Q3"):
                    resp = "1/5"  # 0/3 in Frac
                elif q_ref in ("Q4", "Q5"):
                    resp = q["expected"]
                else:
                    resp = "0"  # 4/10 total

            # 4. Boundary Case: SYN-L6-020 (Rhea Varma)
            # Scores exactly 2/3 in fractions = 66.7% (>= 60%, must NOT trigger review flag)
            elif ref == "SYN-L6-020":
                if q_ref == "Q1":
                    resp = "5/6"  # Correct
                elif q_ref == "Q2":
                    resp = "3/4"  # Correct
                elif q_ref == "Q3":
                    resp = "1/5"  # Incorrect -> 2/3 = 66.7%
                else:
                    resp = q["expected"]  # 9/10 total

            # 5. Completion Concern / Blanks: SYN-L6-021 (Ishaan Joshi)
            # Leaves fractions blank
            elif ref == "SYN-L6-021":
                if q_ref in ("Q1", "Q2", "Q3"):
                    resp = ""  # Unattempted / Blank -> 0 assessed items -> Insufficient Evidence
                else:
                    resp = q["expected"]

            # High achievers: SYN-L6-001 to SYN-L6-010 (9/10 or 10/10)
            elif i <= 10:
                resp = q["expected"]

            # General distribution: mostly secure learners with occasional errors
            else:
                if (i + int(q_ref[1:])) % 7 == 0:
                    resp = "0"  # deterministic incorrect
                else:
                    resp = q["expected"]

            rows.append({
                "learner_ref": ref,
                "question_ref": q_ref,
                "topic_ref": q["topic"],
                "question_text": q["text"],
                "answer_kind": q["kind"],
                "expected_answer": q["expected"],
                "max_marks": q["marks"],
                "response": resp,
            })

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated baseline fixture: {filepath.name} ({len(rows)} response rows)")


def generate_malformed_csvs() -> None:
    """Generates corrupted and boundary fixture files."""
    # 1. Malformed headers
    path_headers = FIXTURES_DIR / "synthetic_class6_malformed_headers.csv"
    with open(path_headers, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student", "q_id", "topic", "answer"])  # Missing required schema columns
        writer.writerow(["SYN-L6-001", "Q1", "MATH-G6-FRAC", "5/6"])

    # 2. Mismatched question metadata
    path_mismatch = FIXTURES_DIR / "synthetic_class6_mismatched_metadata.csv"
    fieldnames = [
        "learner_ref",
        "question_ref",
        "topic_ref",
        "question_text",
        "answer_kind",
        "expected_answer",
        "max_marks",
        "response",
    ]
    with open(path_mismatch, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Row 1 defines Q1 as 5/6
        writer.writerow({
            "learner_ref": "SYN-L6-001",
            "question_ref": "Q1",
            "topic_ref": "MATH-G6-FRAC",
            "question_text": "Evaluate 1/2 + 1/3",
            "answer_kind": "numeric_fraction",
            "expected_answer": "5/6",
            "max_marks": "1.0",
            "response": "5/6",
        })
        # Row 2 conflicts: defines Q1 with different expected_answer "2/3"
        writer.writerow({
            "learner_ref": "SYN-L6-002",
            "question_ref": "Q1",
            "topic_ref": "MATH-G6-FRAC",
            "question_text": "Evaluate 1/2 + 1/3",
            "answer_kind": "numeric_fraction",
            "expected_answer": "2/3",  # CONFLICT!
            "max_marks": "1.0",
            "response": "5/6",
        })

    # 3. Boundary cases (equivalent fraction 2/4 vs 1/2, decimal 0.5 vs 1/2, zero denominator 1/0)
    path_boundary = FIXTURES_DIR / "synthetic_class6_boundary_cases.csv"
    with open(path_boundary, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        cases = [
            ("SYN-L6-001", "Q1", "MATH-G6-FRAC", "Evaluate 1/2 + 1/3", "numeric_fraction", "5/6", "1.0", "10/12"), # Equivalent fraction
            ("SYN-L6-002", "Q4", "MATH-G6-DEC", "Calculate 0.25 + 0.5", "numeric_decimal", "0.75", "1.0", "0.750"), # Equivalent decimal
            ("SYN-L6-003", "Q1", "MATH-G6-FRAC", "Evaluate 1/2 + 1/3", "numeric_fraction", "5/6", "1.0", "1/0"),   # Division by zero
            ("SYN-L6-004", "Q1", "MATH-G6-FRAC", "Evaluate 1/2 + 1/3", "numeric_fraction", "5/6", "1.0", "import os"), # Malicious code string
            ("SYN-L6-005", "Q1", "MATH-G6-FRAC", "Evaluate 1/2 + 1/3", "numeric_fraction", "5/6", "1.0", ""),      # Blank / unattempted
        ]
        for c in cases:
            writer.writerow({
                "learner_ref": c[0],
                "question_ref": c[1],
                "topic_ref": c[2],
                "question_text": c[3],
                "answer_kind": c[4],
                "expected_answer": c[5],
                "max_marks": c[6],
                "response": c[7],
            })

    # 4. Low evidence (only 2 questions in total)
    path_low_evidence = FIXTURES_DIR / "synthetic_low_evidence.csv"
    with open(path_low_evidence, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "learner_ref": "SYN-L6-001",
            "question_ref": "Q1",
            "topic_ref": "MATH-G6-FRAC",
            "question_text": "Evaluate 1/2 + 1/3",
            "answer_kind": "numeric_fraction",
            "expected_answer": "5/6",
            "max_marks": "1.0",
            "response": "2/5",
        })
        writer.writerow({
            "learner_ref": "SYN-L6-001",
            "question_ref": "Q2",
            "topic_ref": "MATH-G6-FRAC",
            "question_text": "Evaluate 1/4 + 1/2",
            "answer_kind": "numeric_fraction",
            "expected_answer": "3/4",
            "max_marks": "1.0",
            "response": "1/3",
        })

    print("✅ Generated malformed, boundary, and low-evidence fixtures.")


def generate_manifest() -> None:
    """Generates the independent expected results manifest."""
    path_manifest = FIXTURES_DIR / "expected_results_manifest.json"

    manifest = {
        "metadata": {
            "scenario": "Class 6 Mathematics Baseline Assessment",
            "class_section": "6-A",
            "total_synthetic_learners": 40,
            "total_questions": 10,
            "review_threshold_rule": "assessed_items >= 3 and percentage < 60.0",
            "insufficient_evidence_rule": "assessed_items < 3",
        },
        "target_learners": {
            "SYN-L6-014": {
                "name": "Aarav Patel",
                "notes": "Primary demo profile: 7/10 overall, 1/3 in fractions",
                "overall": {
                    "total_score": 7.0,
                    "possible_score": 10.0,
                    "percentage": 70.0,
                },
                "topics": {
                    "MATH-G6-FRAC": {
                        "awarded": 1.0,
                        "possible": 3.0,
                        "percentage": 33.33,
                        "assessed_items": 3,
                        "unattempted": 0,
                        "status": "pending_review",
                        "suspected_pattern": "adds_numerators_and_denominators",
                        "flag_reason": "Topic score 33.33% is below 60.0% threshold with 3 assessed items.",
                    },
                    "MATH-G6-DEC": {
                        "awarded": 3.0,
                        "possible": 3.0,
                        "percentage": 100.0,
                        "assessed_items": 3,
                        "unattempted": 0,
                        "status": "secure",
                    },
                    "MATH-G6-PCT": {
                        "awarded": 3.0,
                        "possible": 4.0,
                        "percentage": 75.0,
                        "assessed_items": 4,
                        "unattempted": 0,
                        "status": "secure",
                    },
                },
            },
            "SYN-L6-015": {
                "name": "Diya Sen",
                "notes": "Grouping candidate: identical fraction misconception (1/3 in fractions)",
                "topics": {
                    "MATH-G6-FRAC": {
                        "awarded": 1.0,
                        "possible": 3.0,
                        "percentage": 33.33,
                        "status": "pending_review",
                    }
                },
            },
            "SYN-L6-020": {
                "name": "Rhea Varma",
                "notes": "Boundary score: 2/3 on fractions = 66.7%. Must NOT flag review.",
                "topics": {
                    "MATH-G6-FRAC": {
                        "awarded": 2.0,
                        "possible": 3.0,
                        "percentage": 66.67,
                        "status": "secure",
                    }
                },
            },
            "SYN-L6-021": {
                "name": "Ishaan Joshi",
                "notes": "Blanks / Unattempted: 0 assessed items in fractions. Must flag completion concern, not 0% mastery.",
                "topics": {
                    "MATH-G6-FRAC": {
                        "awarded": 0.0,
                        "possible": 0.0,
                        "percentage": None,
                        "assessed_items": 0,
                        "unattempted": 3,
                        "status": "insufficient_evidence",
                    }
                },
            },
        },
    }

    with open(path_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Generated expected results manifest: {path_manifest.name}")


if __name__ == "__main__":
    generate_baseline_csv()
    generate_malformed_csvs()
    generate_manifest()
