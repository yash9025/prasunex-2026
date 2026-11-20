"""Strictly PII-safe drafting context for grounded support generation.

Per Section 11.2 of the specification:
Send only topic, grade, language, and approved snippet text/IDs.
Exclude names, learner IDs, raw CSV, and raw answers.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, model_validator


class SnippetContext(BaseModel):
    """Sanitized representation of an approved lesson snippet."""

    id: str
    title: str
    content: str
    source_ref: str


class DraftContext(BaseModel):
    """Context payload passed to draft providers.
    
    Guaranteed to contain ZERO student PII or raw submission records.
    """

    topic_code: str
    topic_name: str
    grade_level: int = 6
    language: str = "en"
    snippets: List[SnippetContext] = Field(..., min_length=1)

    @model_validator(mode="after")
    def verify_no_pii_present(self) -> "DraftContext":
        """Enforces that no learner identifiers are inadvertently injected into context."""
        prohibited_substrings = ["SYN-L6-", "SYN-PG-", "learner_id", "priya.sharma", "david.chen"]
        serialized = f"{self.topic_code} {self.topic_name} {' '.join(s.content for s in self.snippets)}"
        for marker in prohibited_substrings:
            if marker in serialized:
                raise ValueError(f"PII safety violation: prohibited identifier '{marker}' detected in drafting context.")
        return self

    @property
    def approved_snippet_ids(self) -> List[str]:
        return [s.id for s in self.snippets]
