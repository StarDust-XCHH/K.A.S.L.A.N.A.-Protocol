"""State-machine events for a call session."""

from __future__ import annotations

from enum import StrEnum

from kaslana.core.states import CallState, InvalidTransitionError, ensure_transition_allowed


class CallEvent(StrEnum):
    START_DIAL = "START_DIAL"
    DIAL_PLACED = "DIAL_PLACED"
    CALL_CONNECTED = "CALL_CONNECTED"
    GREETING_PLAYED = "GREETING_PLAYED"
    USER_SPEECH_CAPTURED = "USER_SPEECH_CAPTURED"
    REPLY_READY = "REPLY_READY"
    SPEECH_PLAYED = "SPEECH_PLAYED"
    HANG_UP = "HANG_UP"
    TIMEOUT = "TIMEOUT"
    FAILURE = "FAILURE"


_EVENT_TRANSITIONS: dict[tuple[CallState, CallEvent], CallState] = {
    (CallState.IDLE, CallEvent.START_DIAL): CallState.DIALING,
    (CallState.DIALING, CallEvent.DIAL_PLACED): CallState.WAITING,
    (CallState.WAITING, CallEvent.CALL_CONNECTED): CallState.GREETING,
    (CallState.GREETING, CallEvent.GREETING_PLAYED): CallState.LISTENING,
    (CallState.LISTENING, CallEvent.USER_SPEECH_CAPTURED): CallState.THINKING,
    (CallState.THINKING, CallEvent.REPLY_READY): CallState.SPEAKING,
    (CallState.SPEAKING, CallEvent.SPEECH_PLAYED): CallState.LISTENING,
}

_TERMINAL_EVENTS = {
    CallEvent.HANG_UP,
    CallEvent.TIMEOUT,
    CallEvent.FAILURE,
}


def next_state_for_event(current_state: CallState, event: CallEvent) -> CallState:
    if current_state is CallState.HUNG_UP:
        if event in _TERMINAL_EVENTS:
            return CallState.HUNG_UP
        raise InvalidTransitionError(f"Cannot process {event} after call is hung up")

    if event in _TERMINAL_EVENTS:
        return CallState.HUNG_UP

    try:
        next_state = _EVENT_TRANSITIONS[(current_state, event)]
    except KeyError as exc:
        raise InvalidTransitionError(f"Invalid event {event} for state {current_state}") from exc

    ensure_transition_allowed(current_state, next_state)
    return next_state
