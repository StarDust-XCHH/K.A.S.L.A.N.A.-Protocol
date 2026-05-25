"""Language model port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ConversationTurn:
    role: Role
    content: str


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str | None = None
    usage: dict[str, int] | None = None


class LlmPort(ABC):
    """Generate assistant replies from conversation context."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
    ) -> LlmResponse:
        """Return one complete model response."""

    async def stream_complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
    ) -> AsyncIterator[str]:
        """Optional streaming LLM extension point."""
        raise NotImplementedError("Streaming LLM is not implemented by this adapter.")
        yield
