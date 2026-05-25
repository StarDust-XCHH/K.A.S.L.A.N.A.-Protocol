from __future__ import annotations

import pytest

from kaslana.core.events import CallEvent, next_state_for_event
from kaslana.core.states import CallState, InvalidTransitionError, can_transition
from kaslana.domain.call_session import CallSession


def test_state_transition_chain_allows_expected_lifecycle() -> None:
    state = CallState.IDLE

    for event, expected in (
        (CallEvent.START_DIAL, CallState.DIALING),
        (CallEvent.DIAL_PLACED, CallState.WAITING),
        (CallEvent.CALL_CONNECTED, CallState.GREETING),
        (CallEvent.GREETING_PLAYED, CallState.LISTENING),
        (CallEvent.USER_SPEECH_CAPTURED, CallState.THINKING),
        (CallEvent.REPLY_READY, CallState.SPEAKING),
        (CallEvent.SPEECH_PLAYED, CallState.LISTENING),
    ):
        state = next_state_for_event(state, event)
        assert state is expected


def test_invalid_event_raises_clear_error() -> None:
    with pytest.raises(InvalidTransitionError):
        next_state_for_event(CallState.IDLE, CallEvent.CALL_CONNECTED)


def test_terminal_event_hangs_up_from_active_state() -> None:
    assert next_state_for_event(CallState.THINKING, CallEvent.FAILURE) is CallState.HUNG_UP
    assert can_transition(CallState.THINKING, CallState.HUNG_UP)


def test_call_session_records_transitions_and_end_reason() -> None:
    session = CallSession.create("wake-target")
    session.apply_event(CallEvent.START_DIAL)
    session.end(reason="manual test end")

    assert session.state is CallState.HUNG_UP
    assert session.ended_at is not None
    assert session.end_reason == "manual test end"
    assert [transition.event for transition in session.transitions] == [
        CallEvent.START_DIAL,
        CallEvent.HANG_UP,
    ]
