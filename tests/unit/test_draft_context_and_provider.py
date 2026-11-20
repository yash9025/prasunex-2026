"""Unit tests for drafting context PII sanitization and provider adapters."""

import pytest
from app.modules.plans.drafting.context import DraftContext, SnippetContext
from app.modules.plans.drafting.provider import (
    GeminiDraftProvider,
    TemplateDraftProvider,
    get_draft_provider,
)
from app.modules.plans.drafting.verifier import DraftValidator


def test_draft_context_rejects_student_pii():
    with pytest.raises(ValueError, match="PII safety violation"):
        DraftContext(
            topic_code="MATH-G6-FRAC",
            topic_name="Fractions",
            snippets=[
                SnippetContext(
                    id="snip-1",
                    title="Student Performance",
                    content="Learner SYN-L6-014 scored low on fractions.",  # Prohibited student ID
                    source_ref="Report",
                )
            ],
        )


def test_template_draft_provider_fractions():
    context = DraftContext(
        topic_code="MATH-G6-FRAC",
        topic_name="Fractions",
        grade_level=6,
        language="en",
        snippets=[
            SnippetContext(
                id="snip-frac-001",
                title="Common Denominators",
                content="To add fractions with unlike denominators...",
                source_ref="Guide",
            )
        ],
    )
    provider = TemplateDraftProvider()
    result = provider.generate(context)

    assert result.generation_mode == "template"
    assert result.is_fallback is False
    assert len(result.draft.practice_items) == 3

    report = DraftValidator.validate(result.draft, context)
    assert report.is_valid is True


def test_template_draft_provider_decimals():
    context = DraftContext(
        topic_code="MATH-G6-DEC",
        topic_name="Decimals",
        grade_level=6,
        language="en",
        snippets=[
            SnippetContext(
                id="snip-dec-001",
                title="Decimal Alignment",
                content="Line up decimal points vertically...",
                source_ref="Guide",
            )
        ],
    )
    provider = TemplateDraftProvider()
    result = provider.generate(context)

    assert result.generation_mode == "template"
    report = DraftValidator.validate(result.draft, context)
    assert report.is_valid is True


def test_gemini_provider_falls_back_when_no_api_key():
    context = DraftContext(
        topic_code="MATH-G6-FRAC",
        topic_name="Fractions",
        grade_level=6,
        language="en",
        snippets=[
            SnippetContext(
                id="snip-frac-001",
                title="Common Denominators",
                content="Content...",
                source_ref="Guide",
            )
        ],
    )
    provider = GeminiDraftProvider(api_key=None)
    result = provider.generate(context)

    assert result.generation_mode == "template"
    assert result.is_fallback is True
    assert "not configured" in result.fallback_reason
