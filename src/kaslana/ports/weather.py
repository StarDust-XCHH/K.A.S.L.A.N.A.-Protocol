"""Weather provider port used by offline prediction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from kaslana.domain.offline_cache import WeatherSnapshot


class WeatherProviderPort(ABC):
    """Provide a lightweight weather snapshot for one target date."""

    @abstractmethod
    async def get_weather(self, target_date: date, location: str) -> WeatherSnapshot:
        """Return weather data without exposing provider-specific response shapes."""
