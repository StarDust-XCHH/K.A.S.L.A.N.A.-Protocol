"""Data ingestion port for local schedule and journal material."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date

from kaslana.domain.offline_cache import IngestedItem


class DataIngestionPort(ABC):
    """Collect local user-authored material for one target date."""

    @abstractmethod
    async def collect(self, target_date: date) -> Sequence[IngestedItem]:
        """Return local items relevant to the nightly prediction job."""
