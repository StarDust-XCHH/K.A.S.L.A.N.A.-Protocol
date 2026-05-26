"""Long-text generation service for the local control panel."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from kaslana.adapters.llm.tongyi_chat import TongyiChatClient, TongyiChatError
from kaslana.core.prompt_manager import LengthTier, PromptManager, ToneStrength
from kaslana.core.text_sanitize import strip_parenthetical_asides


class LlmGenerateError(ValueError):
    """Raised for invalid generation requests."""


@dataclass(frozen=True)
class LongTextGenerateRequest:
    topic: str
    scene: str = ""
    length_tier: LengthTier = "long"
    tone_strength: ToneStrength = "normal"
    user_hint: str = ""


@dataclass(frozen=True)
class LongTextGenerateResult:
    text: str
    model: str
    topic: str
    elapsed_ms: int
    char_count: int
    usage: dict[str, int] | None = None


class LlmGenerateService:
    """Compose Kiana prompts and call the Tongyi urllib client."""

    def __init__(
        self,
        *,
        persona_path: Path,
        client: TongyiChatClient | None = None,
    ) -> None:
        self._prompt_manager = PromptManager.from_yaml(persona_path)
        self._client = client or TongyiChatClient()

    @property
    def client(self) -> TongyiChatClient:
        return self._client

    def status(self) -> dict[str, object]:
        return self._client.get_status().as_dict()

    def generate(self, request: LongTextGenerateRequest) -> LongTextGenerateResult:
        topic = request.topic.strip()
        if not topic:
            raise LlmGenerateError("主题不能为空。")

        length_tier = self._prompt_manager.resolve_length_tier(request.length_tier)
        tone_strength = self._prompt_manager.resolve_tone_strength(request.tone_strength)

        system_prompt = self._prompt_manager.build_system_prompt(
            "long_text_tts",
            length_tier=length_tier,
        )
        user_message = self._prompt_manager.build_user_message(
            topic=topic,
            scene=request.scene,
            length_tier=length_tier,
            tone_strength=tone_strength,
            user_hint=request.user_hint,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        started = time.perf_counter()
        try:
            response = self._client.complete(messages)
        except TongyiChatError as exc:
            raise LlmGenerateError(str(exc)) from exc
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        cleaned_text = strip_parenthetical_asides(response.text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        return LongTextGenerateResult(
            text=cleaned_text,
            model=response.model,
            topic=topic,
            elapsed_ms=elapsed_ms,
            char_count=len(response.text),
            usage=response.usage,
        )
