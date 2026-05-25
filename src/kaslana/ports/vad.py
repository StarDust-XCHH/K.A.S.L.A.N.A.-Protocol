"""Voice activity detection port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from kaslana.ports.audio import AudioChunk


@dataclass(frozen=True)
class SpeechSegment:
    audio: bytes
    sample_rate: int
    channels: int
    start_time_s: float
    end_time_s: float


class VadPort(ABC):
    """Detect speech in a stream and return utterance-sized segments."""

    @abstractmethod
    async def contains_speech(self, chunk: AudioChunk) -> bool:
        """Return true if the chunk contains speech."""

    @abstractmethod
    async def collect_utterance(
        self,
        chunks: AsyncIterator[AudioChunk],
        timeout_s: float,
    ) -> SpeechSegment | None:
        """Collect one utterance, or return none on timeout/silence."""
