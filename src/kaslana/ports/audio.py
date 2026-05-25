"""Audio ports for the physical loopback sound path."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    sample_rate: int
    channels: int
    timestamp_s: float


class AudioInputPort(ABC):
    """Microphone/input stream from phone A's earphone output."""

    @abstractmethod
    async def start(self) -> None:
        """Open the input stream."""

    @abstractmethod
    def stream_chunks(self) -> AsyncIterator[AudioChunk]:
        """Yield PCM chunks until stopped or exhausted."""

    @abstractmethod
    async def stop(self) -> None:
        """Close the input stream."""


class AudioOutputPort(ABC):
    """Speaker/output stream into phone A's microphone input."""

    @abstractmethod
    async def play_file(self, path: Path) -> None:
        """Play an audio file through the configured output device."""

    @abstractmethod
    async def play_pcm(self, audio: bytes, sample_rate: int, channels: int) -> None:
        """Play PCM bytes through the configured output device."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop output playback."""
