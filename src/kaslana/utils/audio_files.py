"""Audio file path helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_audio_path(path: Path, root: Path | None = None) -> Path:
    if path.is_absolute():
        return path
    return (root or Path.cwd()) / path
