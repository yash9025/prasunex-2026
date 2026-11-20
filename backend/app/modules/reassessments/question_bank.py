"""Fresh diagnostic reassessment question bank per Section 12.3.

Provides fresh, teacher-approved question items deterministically selected
for each curriculum topic. Excludes baseline assessment questions and
intervention practice items to avoid recall bias.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class QuestionBankItem(BaseModel):
    """Teacher-approved fresh diagnostic item with server-side answer key."""

    question_ref: str
    topic_code: str
    question_text: str
    answer_kind: str = "numeric_fraction"
    expected_answer: str
    max_marks: float = 1.0
    rationale: str


class FreshQuestionBank:
    """Curated repository of fresh diagnostic items."""

    _ITEMS: Dict[str, List[QuestionBankItem]] = {
        "MATH-G6-FRAC": [
            QuestionBankItem(
                question_ref="Q-RE-FRAC-01",
                topic_code="MATH-G6-FRAC",
                question_text="Calculate 1/4 + 1/3. Express your answer as a simplified fraction.",
                answer_kind="numeric_fraction",
                expected_answer="7/12",
                max_marks=1.0,
                rationale="Find common denominator of 12: 1/4 = 3/12, 1/3 = 4/12. 3/12 + 4/12 = 7/12.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-FRAC-02",
                topic_code="MATH-G6-FRAC",
                question_text="Calculate 2/3 + 1/6. Express your answer as a simplified fraction.",
                answer_kind="numeric_fraction",
                expected_answer="5/6",
                max_marks=1.0,
                rationale="Find common denominator of 6: 2/3 = 4/6. 4/6 + 1/6 = 5/6.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-FRAC-03",
                topic_code="MATH-G6-FRAC",
                question_text="Calculate 3/8 + 1/4. Express your answer as a simplified fraction.",
                answer_kind="numeric_fraction",
                expected_answer="5/8",
                max_marks=1.0,
                rationale="Find common denominator of 8: 1/4 = 2/8. 3/8 + 2/8 = 5/8.",
            ),
        ],
        "MATH-G6-DEC": [
            QuestionBankItem(
                question_ref="Q-RE-DEC-01",
                topic_code="MATH-G6-DEC",
                question_text="Calculate 0.65 + 0.3. Express your answer as a decimal.",
                answer_kind="numeric_decimal",
                expected_answer="0.95",
                max_marks=1.0,
                rationale="Align decimal places: 0.65 + 0.30 = 0.95.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-DEC-02",
                topic_code="MATH-G6-DEC",
                question_text="Calculate 1.8 - 0.45. Express your answer as a decimal.",
                answer_kind="numeric_decimal",
                expected_answer="1.35",
                max_marks=1.0,
                rationale="Align decimal places: 1.80 - 0.45 = 1.35.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-DEC-03",
                topic_code="MATH-G6-DEC",
                question_text="Calculate 0.25 + 0.5. Express your answer as a decimal.",
                answer_kind="numeric_decimal",
                expected_answer="0.75",
                max_marks=1.0,
                rationale="Align decimal places: 0.25 + 0.50 = 0.75.",
            ),
        ],
        "MATH-G6-PCT": [
            QuestionBankItem(
                question_ref="Q-RE-PCT-01",
                topic_code="MATH-G6-PCT",
                question_text="Calculate 40% + 35%. Express your answer as a percentage.",
                answer_kind="numeric_percentage",
                expected_answer="75%",
                max_marks=1.0,
                rationale="40% + 35% = 75%.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-PCT-02",
                topic_code="MATH-G6-PCT",
                question_text="Calculate 80% - 30%. Express your answer as a percentage.",
                answer_kind="numeric_percentage",
                expected_answer="50%",
                max_marks=1.0,
                rationale="80% - 30% = 50%.",
            ),
            QuestionBankItem(
                question_ref="Q-RE-PCT-03",
                topic_code="MATH-G6-PCT",
                question_text="Calculate 15% + 35%. Express your answer as a percentage.",
                answer_kind="numeric_percentage",
                expected_answer="50%",
                max_marks=1.0,
                rationale="15% + 35% = 50%.",
            ),
        ],
    }

    @classmethod
    def get_fresh_items(cls, topic_code: str) -> List[QuestionBankItem]:
        """Returns fresh assessment items for the topic, ensuring non-overlap."""
        return cls._ITEMS.get(topic_code, cls._ITEMS["MATH-G6-FRAC"])

    @classmethod
    def find_item_by_ref(cls, topic_code: str, question_ref: str) -> Optional[QuestionBankItem]:
        items = cls.get_fresh_items(topic_code)
        for item in items:
            if item.question_ref == question_ref:
                return item
        return None
