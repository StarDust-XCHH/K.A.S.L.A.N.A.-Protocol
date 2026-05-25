"""Speech-to-text port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from kaslana.ports.audio import AudioChunk
from kaslana.ports.vad import SpeechSegment


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str | None = None
    confidence: float | None = None


class AsrPort(ABC):
    """Convert speech audio into text."""

    @abstractmethod
    async def transcribe(self, segment: SpeechSegment) -> Transcript:
        """Transcribe a complete utterance."""

    async def transcribe_stream(
        self,
        chunks: AsyncIterator[AudioChunk],
    ) -> AsyncIterator[Transcript]:
        """Optional streaming ASR extension point."""
        raise NotImplementedError("Streaming ASR is not implemented by this adapter.")
        yield
