"""GPT-SoVITS TTS adapter placeholder."""

from __future__ import annotations

from kaslana.ports.tts import TtsAudio, TtsPort


class GptSovitsTts(TtsPort):
    """Future adapter for a local GPT-SoVITS service."""

    async def synthesize(self, text: str) -> TtsAudio:
        raise NotImplementedError("GPT-SoVITS synthesize is not implemented yet.")
