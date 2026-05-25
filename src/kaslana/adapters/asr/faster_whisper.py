"""Faster-Whisper ASR adapter placeholder."""

from __future__ import annotations

from kaslana.ports.asr import AsrPort, Transcript
from kaslana.ports.vad import SpeechSegment


class FasterWhisperAsr(AsrPort):
    """Future Faster-Whisper-backed ASR adapter."""

    async def transcribe(self, segment: SpeechSegment) -> Transcript:
        raise NotImplementedError("Faster-Whisper transcribe is not implemented yet.")
