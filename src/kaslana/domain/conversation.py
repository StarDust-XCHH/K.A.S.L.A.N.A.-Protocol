"""Conversation context passed into the language model port."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from kaslana.ports.llm import ConversationTurn

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ConversationMessage:
    role: Role
    content: str


@dataclass
class ConversationContext:
    system_prompt: str
    messages: list[ConversationMessage] = field(default_factory=list)

    def append_user(self, content: str) -> None:
        self.messages.append(ConversationMessage(role="user", content=content))

    def append_assistant(self, content: str) -> None:
        self.messages.append(ConversationMessage(role="assistant", content=content))

    def to_llm_turns(self) -> list[ConversationTurn]:
        return [
            ConversationTurn(role=message.role, content=message.content)
            for message in self.messages
        ]
