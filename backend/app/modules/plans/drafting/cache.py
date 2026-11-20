"""Candidate draft caching per Section 11.3.

Caches candidates by school, topic, grade, source-content hash, prompt version,
provider configuration, and language. Cache hits still require explicit teacher review.
"""

import hashlib
import json
from typing import Dict, Optional
from app.modules.plans.drafting.verifier import DraftContent


class DraftCandidateCache:
    """In-memory candidate cache for generated support drafts."""

    _cache: Dict[str, dict] = {}

    @classmethod
    def compute_cache_key(
        cls,
        school_id: str,
        topic_code: str,
        grade_level: int,
        language: str,
        snippet_ids: list[str],
        prompt_version: str = "v1.0",
        provider_name: str = "template",
    ) -> str:
        payload = {
            "school_id": school_id,
            "topic_code": topic_code,
            "grade_level": grade_level,
            "language": language,
            "snippet_ids": sorted(snippet_ids),
            "prompt_version": prompt_version,
            "provider_name": provider_name,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, cache_key: str) -> Optional[dict]:
        return cls._cache.get(cache_key)

    @classmethod
    def set(cls, cache_key: str, data: dict) -> None:
        cls._cache[cache_key] = data

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
