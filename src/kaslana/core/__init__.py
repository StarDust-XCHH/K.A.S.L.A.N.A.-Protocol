"""Core call lifecycle orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kaslana.core.events import CallEvent
    from kaslana.core.offline_preprocessor import (
        OfflinePreprocessOptions,
        OfflinePreprocessor,
        OfflinePreprocessorDependencies,
    )
    from kaslana.core.orchestrator import Orchestrator, OrchestratorDependencies, RunOptions
    from kaslana.core.states import CallState, InvalidTransitionError

__all__ = [
    "CallEvent",
    "CallState",
    "InvalidTransitionError",
    "OfflinePreprocessor",
    "OfflinePreprocessorDependencies",
    "OfflinePreprocessOptions",
    "Orchestrator",
    "OrchestratorDependencies",
    "RunOptions",
    "next_state_for_event",
]


def __getattr__(name: str) -> Any:
    if name in {"CallEvent", "next_state_for_event"}:
        from kaslana.core.events import CallEvent, next_state_for_event

        return {"CallEvent": CallEvent, "next_state_for_event": next_state_for_event}[name]
    if name in {"CallState", "InvalidTransitionError"}:
        from kaslana.core.states import CallState, InvalidTransitionError

        return {"CallState": CallState, "InvalidTransitionError": InvalidTransitionError}[name]
    if name in {"Orchestrator", "OrchestratorDependencies", "RunOptions"}:
        from kaslana.core.orchestrator import Orchestrator, OrchestratorDependencies, RunOptions

        return {
            "Orchestrator": Orchestrator,
            "OrchestratorDependencies": OrchestratorDependencies,
            "RunOptions": RunOptions,
        }[name]
    if name in {
        "OfflinePreprocessor",
        "OfflinePreprocessorDependencies",
        "OfflinePreprocessOptions",
    }:
        from kaslana.core.offline_preprocessor import (
            OfflinePreprocessOptions,
            OfflinePreprocessor,
            OfflinePreprocessorDependencies,
        )

        return {
            "OfflinePreprocessor": OfflinePreprocessor,
            "OfflinePreprocessorDependencies": OfflinePreprocessorDependencies,
            "OfflinePreprocessOptions": OfflinePreprocessOptions,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
