"""Silero VAD adapter placeholder."""

from __future__ import annotations

from collections.abc import AsyncIterator

from kaslana.ports.audio import AudioChunk
from kaslana.ports.vad import SpeechSegment, VadPort


class SileroVad(VadPort):
    """Future Silero-backed VAD adapter."""

    async def contains_speech(self, chunk: AudioChunk) -> bool:
        raise NotImplementedError("Silero contains_speech is not implemented yet.")

    async def collect_utterance(
        self,
        chunks: AsyncIterator[AudioChunk],
        timeout_s: float,
    ) -> SpeechSegment | None:
        raise NotImplementedError("Silero collect_utterance is not implemented yet.")
