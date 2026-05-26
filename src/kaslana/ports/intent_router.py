"""Local intent router port for cache-first replies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from kaslana.domain.offline_cache import CachedDialogueMapping, IntentMatch


class IntentRouterPort(ABC):
    """Match a user transcript to one pre-rendered dialogue branch."""

    @abstractmethod
    def match(self, transcript: str, mapping: CachedDialogueMapping) -> IntentMatch:
        """Return the best cache branch match for a transcript."""
