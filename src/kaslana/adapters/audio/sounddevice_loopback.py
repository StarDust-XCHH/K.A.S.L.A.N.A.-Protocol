"""sounddevice loopback adapter placeholders."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from kaslana.ports.audio import AudioChunk, AudioInputPort, AudioOutputPort


class SoundDeviceAudioInput(AudioInputPort):
    """Future adapter for the PC input connected to phone A audio output."""

    async def start(self) -> None:
        raise NotImplementedError("sounddevice audio input start is not implemented yet.")

    def stream_chunks(self) -> AsyncIterator[AudioChunk]:
        raise NotImplementedError("sounddevice audio input streaming is not implemented yet.")

    async def stop(self) -> None:
        raise NotImplementedError("sounddevice audio input stop is not implemented yet.")


class SoundDeviceAudioOutput(AudioOutputPort):
    """Future adapter for PC output connected to phone A microphone input."""

    async def play_file(self, path: Path) -> None:
        raise NotImplementedError("sounddevice play_file is not implemented yet.")

    async def play_pcm(self, audio: bytes, sample_rate: int, channels: int) -> None:
        raise NotImplementedError("sounddevice play_pcm is not implemented yet.")

    async def stop(self) -> None:
        raise NotImplementedError("sounddevice audio output stop is not implemented yet.")
