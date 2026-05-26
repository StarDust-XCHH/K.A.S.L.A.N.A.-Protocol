"""Dialogue cache port for pre-rendered offline branches."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from kaslana.domain.offline_cache import CachedDialogueMapping


class DialogueCachePort(ABC):
    """Load and save daily pre-rendered dialogue mappings."""

    @abstractmethod
    async def load_mapping(self, target_date: date) -> CachedDialogueMapping | None:
        """Return the cached mapping for the date, or None when absent."""

    @abstractmethod
    async def save_mapping(self, mapping: CachedDialogueMapping) -> None:
        """Persist a cached mapping."""
