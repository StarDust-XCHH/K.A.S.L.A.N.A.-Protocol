"""Call lifecycle states and transition validation."""

from __future__ import annotations

from enum import StrEnum


class CallState(StrEnum):
    IDLE = "IDLE"
    DIALING = "DIALING"
    WAITING = "WAITING"
    GREETING = "GREETING"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    HUNG_UP = "HUNG_UP"


class InvalidTransitionError(RuntimeError):
    """Raised when the call state machine receives an impossible transition."""


ALLOWED_TRANSITIONS: dict[CallState, frozenset[CallState]] = {
    CallState.IDLE: frozenset({CallState.DIALING, CallState.HUNG_UP}),
    CallState.DIALING: frozenset({CallState.WAITING, CallState.HUNG_UP}),
    CallState.WAITING: frozenset({CallState.GREETING, CallState.HUNG_UP}),
    CallState.GREETING: frozenset({CallState.LISTENING, CallState.HUNG_UP}),
    CallState.LISTENING: frozenset({CallState.THINKING, CallState.HUNG_UP}),
    CallState.THINKING: frozenset({CallState.SPEAKING, CallState.HUNG_UP}),
    CallState.SPEAKING: frozenset({CallState.LISTENING, CallState.HUNG_UP}),
    CallState.HUNG_UP: frozenset(),
}


def can_transition(from_state: CallState, to_state: CallState) -> bool:
    return to_state in ALLOWED_TRANSITIONS[from_state]


def ensure_transition_allowed(from_state: CallState, to_state: CallState) -> None:
    if not can_transition(from_state, to_state):
        raise InvalidTransitionError(f"Invalid call transition: {from_state} -> {to_state}")
