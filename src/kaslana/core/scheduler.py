"""Scheduler skeleton for future timed wake-up calls."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from kaslana.core.orchestrator import Orchestrator, RunOptions
from kaslana.domain.call_session import CallSession


@dataclass(frozen=True)
class MorningSchedule:
    wake_time: str
    enabled: bool = False
    poll_interval_s: float = 30.0


class MorningCallScheduler:
    """Small wrapper reserved for time-based orchestration."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        options_factory: Callable[[], RunOptions],
    ) -> None:
        self._orchestrator = orchestrator
        self._options_factory = options_factory

    async def run_once(self) -> CallSession:
        return await self._orchestrator.run_morning_call(self._options_factory())

    async def run_forever(self, schedule: MorningSchedule) -> None:
        if not schedule.enabled:
            return
        while True:
            await asyncio.sleep(schedule.poll_interval_s)
