"""Text-to-speech port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class TtsAudio:
    audio: bytes
    sample_rate: int
    channels: int
    format: str = "pcm_s16le"


class TtsPort(ABC):
    """Render text into assistant voice audio."""

    @abstractmethod
    async def synthesize(self, text: str) -> TtsAudio:
        """Synthesize a complete response."""

    async def stream_synthesize(self, text: str) -> AsyncIterator[TtsAudio]:
        """Optional streaming TTS extension point."""
        raise NotImplementedError("Streaming TTS is not implemented by this adapter.")
        yield
