"""Static weather provider used until a real API adapter is selected."""

from __future__ import annotations

from datetime import date

from kaslana.domain.offline_cache import WeatherSnapshot
from kaslana.ports.weather import WeatherProviderPort


class StaticWeatherProvider(WeatherProviderPort):
    """Return configured placeholder weather data without network access."""

    def __init__(self, summary: str = "", temperature_c: float | None = None) -> None:
        self._summary = summary
        self._temperature_c = temperature_c

    async def get_weather(self, target_date: date, location: str) -> WeatherSnapshot:
        return WeatherSnapshot(
            target_date=target_date,
            location=location,
            summary=self._summary,
            temperature_c=self._temperature_c,
        )
