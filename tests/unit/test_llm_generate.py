from __future__ import annotations

from pathlib import Path

import pytest

from kaslana.adapters.llm.tongyi_chat import TongyiChatClient, TongyiChatResult
from kaslana.services.llm_generate import (
    LlmGenerateError,
    LlmGenerateService,
    LongTextGenerateRequest,
)


class ScriptedClient(TongyiChatClient):
    def __init__(self, text: str) -> None:
        super().__init__(api_key="test-key")
        self._text = text

    def complete(self, messages: list[dict[str, str]]) -> TongyiChatResult:
        assert "《崩坏三》" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        return TongyiChatResult(
            text=self._text,
            model="qwen-long",
            usage={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        )


def test_generate_builds_kiana_prompt() -> None:
    service = LlmGenerateService(
        persona_path=Path("config/prompts/kiana.yaml"),
        client=ScriptedClient("这是一段琪亚娜风格的长文。"),
    )

    result = service.generate(
        LongTextGenerateRequest(
            topic="今天的训练",
            user_hint="提到芽衣",
            length_tier="long",
            tone_strength="high",
        )
    )

    assert result.topic == "今天的训练"
    assert "琪亚娜" in result.text
    assert result.elapsed_ms >= 0
    assert result.char_count == len(result.text)
    assert result.usage is not None


def test_generate_strips_parenthetical_asides() -> None:
    service = LlmGenerateService(
        persona_path=Path("config/prompts/kiana.yaml"),
        client=ScriptedClient("早安呀（心里有点紧张）该起床啦。"),
    )

    result = service.generate(LongTextGenerateRequest(topic="早安"))

    assert result.text == "早安呀该起床啦。"


def test_generate_rejects_empty_topic() -> None:
    service = LlmGenerateService(
        persona_path=Path("config/prompts/kiana.yaml"),
        client=ScriptedClient("ignored"),
    )

    with pytest.raises(LlmGenerateError, match="主题"):
        service.generate(LongTextGenerateRequest(topic="   "))
