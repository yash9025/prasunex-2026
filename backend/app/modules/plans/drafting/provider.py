"""Provider-independent support drafting engine per Section 11.2 & 11.3.

Supports:
1. Grounded template generation (deterministic, zero external network dependency).
2. Gemini live AI drafting adapter (isolated, PII-free prompt, zero model tools).
3. Graceful fallback on timeout, missing keys, or validation rejection.
"""

from abc import ABC, abstractmethod
import json
import logging
from typing import Literal, Optional
from urllib import request as urllib_request
from urllib.error import URLError

from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.plans.drafting.context import DraftContext
from app.modules.plans.drafting.verifier import (
    DraftContent,
    DraftValidator,
    MathSpec,
    PracticeItem,
)

logger = logging.getLogger(__name__)


class DraftGenerationResult(BaseModel):
    """Output envelope from any draft provider."""

    draft: DraftContent
    generation_mode: Literal["ai", "template"]
    provider_name: str
    prompt_version: str = "v1.0"
    is_fallback: bool = False
    fallback_reason: Optional[str] = None


class DraftProvider(ABC):
    """Abstract provider interface for generating grounded support materials."""

    @abstractmethod
    def generate(self, context: DraftContext) -> DraftGenerationResult:
        """Generates draft intervention content from safe curriculum context."""
        pass


class TemplateDraftProvider(DraftProvider):
    """Deterministic, curriculum-aligned template provider.
    
    Guarantees mathematically verified practice items and verified citations.
    """

    PROVIDER_NAME = "curriculum-template"
    PROMPT_VERSION = "v1.0-template"

    def generate(self, context: DraftContext) -> DraftGenerationResult:
        topic_code = context.topic_code
        source_ids = context.approved_snippet_ids[:2]  # cite up to 2 approved sources

        if "FRAC" in topic_code:
            explanation = (
                "When adding fractions with unlike denominators, we cannot add numerators and denominators together. "
                "Instead, we must first find a common denominator by calculating the least common multiple of the denominators, "
                "convert each fraction to an equivalent form with that common denominator, and then add the numerators while "
                "keeping the common denominator unchanged."
            )
            practice_items = [
                PracticeItem(
                    item_num=1,
                    question_text="Calculate 1/3 + 1/6. Express your answer as a simplified fraction.",
                    math_spec=MathSpec(operation="add", operands=["1/3", "1/6"], answer_format="fraction"),
                    expected_answer="1/2",
                    rationale="Find a common denominator of 6: 1/3 = 2/6. Then 2/6 + 1/6 = 3/6 = 1/2.",
                ),
                PracticeItem(
                    item_num=2,
                    question_text="Calculate 1/4 + 1/2. Express your answer as a simplified fraction.",
                    math_spec=MathSpec(operation="add", operands=["1/4", "1/2"], answer_format="fraction"),
                    expected_answer="3/4",
                    rationale="Find a common denominator of 4: 1/2 = 2/4. Then 1/4 + 2/4 = 3/4.",
                ),
                PracticeItem(
                    item_num=3,
                    question_text="Calculate 2/5 + 1/10. Express your answer as a simplified fraction.",
                    math_spec=MathSpec(operation="add", operands=["2/5", "1/10"], answer_format="fraction"),
                    expected_answer="1/2",
                    rationale="Find a common denominator of 10: 2/5 = 4/10. Then 4/10 + 1/10 = 5/10 = 1/2.",
                ),
            ]
        elif "DEC" in topic_code:
            explanation = (
                "To add and subtract decimals accurately, write the numbers vertically with their decimal points in a straight line. "
                "This guarantees that place values correspond correctly (tenths with tenths, hundredths with hundredths). "
                "Append trailing zeros if necessary to align columns."
            )
            practice_items = [
                PracticeItem(
                    item_num=1,
                    question_text="Calculate 0.75 + 0.25. Express your answer as a decimal.",
                    math_spec=MathSpec(operation="add", operands=["0.75", "0.25"], answer_format="decimal"),
                    expected_answer="1.0",
                    rationale="Align decimal points vertically: 0.75 + 0.25 = 1.00 = 1.0.",
                ),
                PracticeItem(
                    item_num=2,
                    question_text="Calculate 0.4 + 0.35. Express your answer as a decimal.",
                    math_spec=MathSpec(operation="add", operands=["0.4", "0.35"], answer_format="decimal"),
                    expected_answer="0.75",
                    rationale="Rewrite 0.4 as 0.40. Align decimal points: 0.40 + 0.35 = 0.75.",
                ),
                PracticeItem(
                    item_num=3,
                    question_text="Calculate 1.5 - 0.25. Express your answer as a decimal.",
                    math_spec=MathSpec(operation="subtract", operands=["1.5", "0.25"], answer_format="decimal"),
                    expected_answer="1.25",
                    rationale="Rewrite 1.5 as 1.50. Align decimal points: 1.50 - 0.25 = 1.25.",
                ),
            ]
        else:  # Percentages
            explanation = (
                "A percentage represents a ratio per hundred. To perform calculations with percentages, "
                "remember that P% means P/100. When adding percentage rates, combine like terms and express "
                "the result in standard percentage or simplified fraction form."
            )
            practice_items = [
                PracticeItem(
                    item_num=1,
                    question_text="Calculate 50% + 25%. Express your answer as a percentage.",
                    math_spec=MathSpec(operation="add", operands=["50%", "25%"], answer_format="percentage"),
                    expected_answer="75%",
                    rationale="50% + 25% = 75% (equivalent to 1/2 + 1/4 = 3/4 = 75%).",
                ),
                PracticeItem(
                    item_num=2,
                    question_text="Calculate 75% - 25%. Express your answer as a percentage.",
                    math_spec=MathSpec(operation="subtract", operands=["75%", "25%"], answer_format="percentage"),
                    expected_answer="50%",
                    rationale="75% - 25% = 50% (equivalent to 3/4 - 1/4 = 2/4 = 1/2 = 50%).",
                ),
                PracticeItem(
                    item_num=3,
                    question_text="Calculate 20% + 30%. Express your answer as a percentage.",
                    math_spec=MathSpec(operation="add", operands=["20%", "30%"], answer_format="percentage"),
                    expected_answer="50%",
                    rationale="20% + 30% = 50% (equivalent to 2/10 + 3/10 = 5/10 = 1/2 = 50%).",
                ),
            ]

        draft = DraftContent(
            topic_code=topic_code,
            source_ids=source_ids,
            explanation=explanation,
            practice_items=practice_items,
        )

        return DraftGenerationResult(
            draft=draft,
            generation_mode="template",
            provider_name=self.PROVIDER_NAME,
            prompt_version=self.PROMPT_VERSION,
            is_fallback=False,
            fallback_reason=None,
        )


class GeminiDraftProvider(DraftProvider):
    """Google Gemini AI drafting provider with strict grounding and fallback."""

    PROVIDER_NAME = "google-gemini"
    PROMPT_VERSION = "v1.0-gemini"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.template_fallback = TemplateDraftProvider()

    def generate(self, context: DraftContext) -> DraftGenerationResult:
        if not self.api_key:
            logger.info("Gemini API key not configured. Using deterministic curriculum template.")
            res = self.template_fallback.generate(context)
            res.is_fallback = True
            res.fallback_reason = "Gemini API key not configured in environment. Using verified curriculum template."
            return res

        # Build strictly PII-free prompt
        snippet_texts = "\n---\n".join([f"Source [{s.id}] {s.title}:\n{s.content}" for s in context.snippets])
        prompt = f"""You are an expert Grade 6 Mathematics curriculum specialist.
Your task is to generate a grounded intervention draft for Grade {context.grade_level} Topic '{context.topic_name}' ({context.topic_code}).
Use ONLY the approved curriculum sources below. Do not introduce ungrounded facts.

APPROVED SOURCES:
{snippet_texts}

REQUIREMENTS:
1. Write a clear pedagogical explanation (1-2 paragraphs) explaining the core concept.
2. Provide EXACTLY 3 numeric practice items.
3. For each practice item, provide:
   - item_num: 1, 2, or 3
   - question_text: clear question mentioning both operands
   - math_spec: {{"operation": "add"|"subtract"|"multiply"|"divide", "operands": ["op1", "op2"], "answer_format": "fraction"|"decimal"|"percentage"}}
   - expected_answer: exact string representation
   - rationale: step-by-step solution
4. Return ONLY valid JSON adhering to this schema:
{{
  "topic_code": "{context.topic_code}",
  "source_ids": {json.dumps(context.approved_snippet_ids[:2])},
  "explanation": "...",
  "practice_items": [
     {{
       "item_num": 1,
       "question_text": "...",
       "math_spec": {{"operation": "add", "operands": ["1/3", "1/6"], "answer_format": "fraction"}},
       "expected_answer": "1/2",
       "rationale": "..."
     }}
  ]
}}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.DRAFTING_MODEL}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"},
        }

        try:
            req = urllib_request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=settings.DRAFTING_TIMEOUT_SECONDS) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_content)
                    draft = DraftContent(**parsed)
                    
                    # Verify math
                    report = DraftValidator.validate(draft, context)
                    if not report.is_valid:
                        logger.warning("Gemini output failed mathematical verification: %s. Falling back to template.", report.errors)
                        res = self.template_fallback.generate(context)
                        res.is_fallback = True
                        res.fallback_reason = f"AI output failed mathematical verification: {'; '.join(report.errors)}"
                        return res

                    return DraftGenerationResult(
                        draft=draft,
                        generation_mode="ai",
                        provider_name=self.PROVIDER_NAME,
                        prompt_version=self.PROMPT_VERSION,
                        is_fallback=False,
                    )
        except Exception as exc:
            logger.warning("Gemini live drafting failed (%s). Gracefully falling back to curriculum template.", str(exc))
            res = self.template_fallback.generate(context)
            res.is_fallback = True
            res.fallback_reason = f"AI service unavailable or timed out ({str(exc)}). Used verified curriculum template."
            return res

        # Fallback if unreached
        res = self.template_fallback.generate(context)
        res.is_fallback = True
        res.fallback_reason = "Using verified curriculum template."
        return res


def get_draft_provider(mode: str = "auto") -> DraftProvider:
    """Factory selecting the appropriate drafting provider."""
    if mode == "template":
        return TemplateDraftProvider()
    if mode == "ai" or mode == "auto":
        return GeminiDraftProvider()
    return TemplateDraftProvider()
