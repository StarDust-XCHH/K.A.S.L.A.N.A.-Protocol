"""OpenAI-compatible chat completion adapter placeholder."""

from __future__ import annotations

from collections.abc import Sequence

from kaslana.ports.llm import ConversationTurn, LlmPort, LlmResponse


class OpenAICompatibleLlm(LlmPort):
    """Future adapter for OpenAI-compatible chat completion APIs."""

    async def complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
    ) -> LlmResponse:
        raise NotImplementedError("OpenAI-compatible LLM complete is not implemented yet.")
