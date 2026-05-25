"""Call session domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from kaslana.core.events import CallEvent, next_state_for_event
from kaslana.core.states import CallState


@dataclass(frozen=True)
class StateTransition:
    from_state: CallState
    to_state: CallState
    event: CallEvent
    occurred_at: datetime
    reason: str | None = None


@dataclass
class CallSession:
    session_id: str
    contact_alias: str
    state: CallState = CallState.IDLE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    end_reason: str | None = None
    failure_reason: str | None = None
    transitions: list[StateTransition] = field(default_factory=list)

    @classmethod
    def create(cls, contact_alias: str) -> CallSession:
        return cls(session_id=str(uuid4()), contact_alias=contact_alias)

    def apply_event(self, event: CallEvent, reason: str | None = None) -> CallState:
        next_state = next_state_for_event(self.state, event)
        transition = StateTransition(
            from_state=self.state,
            to_state=next_state,
            event=event,
            occurred_at=datetime.now(UTC),
            reason=reason,
        )
        self.transitions.append(transition)
        self.state = next_state

        if event is CallEvent.FAILURE:
            self.failure_reason = reason or "unknown failure"

        if next_state is CallState.HUNG_UP and self.ended_at is None:
            self.ended_at = transition.occurred_at
            self.end_reason = reason or event.value

        return self.state

    def end(self, reason: str | None = None) -> None:
        self.apply_event(CallEvent.HANG_UP, reason=reason)
