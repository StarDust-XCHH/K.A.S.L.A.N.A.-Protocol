"""Domain objects for offline dialogue prediction and cache lookup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

IngestedItemKind = Literal["markdown", "text", "json"]


@dataclass(frozen=True)
class IngestedItem:
    source: Path
    content: str
    kind: IngestedItemKind
    target_date: date


@dataclass(frozen=True)
class WeatherSnapshot:
    target_date: date
    location: str
    summary: str = ""
    temperature_c: float | None = None


@dataclass(frozen=True)
class DialogueBranch:
    branch_id: str
    intent: str
    text: str
    audio_path: Path | None = None
    patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class DialogueStateTree:
    target_date: date
    greeting_text: str
    branches: tuple[DialogueBranch, ...]
    weather: WeatherSnapshot | None = None
    source_count: int = 0


@dataclass(frozen=True)
class CachedDialogueMapping:
    target_date: date
    greeting_text: str
    greeting_audio_path: Path
    branches: tuple[DialogueBranch, ...]
    schema_version: int = 1

    def branch_by_id(self, branch_id: str) -> DialogueBranch | None:
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        return None


@dataclass(frozen=True)
class IntentMatch:
    branch_id: str | None
    confidence: float
    matched: bool
    audio_path: Path | None = None
    reason: str = ""
