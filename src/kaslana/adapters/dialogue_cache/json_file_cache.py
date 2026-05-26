"""JSON-file dialogue cache adapter."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch
from kaslana.ports.dialogue_cache import DialogueCachePort


class JsonDialogueCache(DialogueCachePort):
    """Store one state mapping per day under cache/YYYY-MM-DD/state_mapping.json."""

    def __init__(self, root_dir: Path | str = Path("cache")) -> None:
        self._root_dir = Path(root_dir)

    async def load_mapping(self, target_date: date) -> CachedDialogueMapping | None:
        mapping_path = self._mapping_path(target_date)
        if not mapping_path.exists():
            return None

        try:
            raw = json.loads(mapping_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid dialogue cache JSON: {mapping_path}") from exc

        return self._mapping_from_raw(raw, target_date, mapping_path.parent)

    async def save_mapping(self, mapping: CachedDialogueMapping) -> None:
        day_dir = self._day_dir(mapping.target_date)
        day_dir.mkdir(parents=True, exist_ok=True)
        payload = self._mapping_to_raw(mapping, day_dir)
        self._mapping_path(mapping.target_date).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _day_dir(self, target_date: date) -> Path:
        return self._root_dir / target_date.isoformat()

    def _mapping_path(self, target_date: date) -> Path:
        return self._day_dir(target_date) / "state_mapping.json"

    def _mapping_from_raw(
        self,
        raw: Any,
        fallback_date: date,
        day_dir: Path,
    ) -> CachedDialogueMapping:
        if not isinstance(raw, dict):
            raise ValueError("Dialogue cache mapping must be a JSON object.")

        schema_version = _int(raw, "schema_version")
        if schema_version != 1:
            raise ValueError(f"Unsupported dialogue cache schema version: {schema_version}")

        raw_date = raw.get("date", fallback_date.isoformat())
        if not isinstance(raw_date, str):
            raise ValueError("Dialogue cache date must be a string.")
        target_date = date.fromisoformat(raw_date)

        greeting = _mapping(raw, "greeting")
        greeting_text = _str(greeting, "text")
        greeting_audio_path = _resolve_cache_path(day_dir, _str(greeting, "audio_path"))

        branches_raw = raw.get("branches")
        if not isinstance(branches_raw, list):
            raise ValueError("Dialogue cache branches must be a list.")

        branches = tuple(
            DialogueBranch(
                branch_id=_str(branch, "id"),
                intent=_str(branch, "intent"),
                text=_str(branch, "text"),
                audio_path=_resolve_cache_path(day_dir, _str(branch, "audio_path")),
                patterns=_patterns(branch.get("patterns", [])),
            )
            for branch in branches_raw
            if isinstance(branch, dict)
        )
        if len(branches) != len(branches_raw):
            raise ValueError("Dialogue cache branches must contain only JSON objects.")

        return CachedDialogueMapping(
            target_date=target_date,
            greeting_text=greeting_text,
            greeting_audio_path=greeting_audio_path,
            branches=branches,
            schema_version=schema_version,
        )

    def _mapping_to_raw(self, mapping: CachedDialogueMapping, day_dir: Path) -> dict[str, Any]:
        return {
            "schema_version": mapping.schema_version,
            "date": mapping.target_date.isoformat(),
            "greeting": {
                "text": mapping.greeting_text,
                "audio_path": _relative_cache_path(day_dir, mapping.greeting_audio_path),
            },
            "branches": [
                {
                    "id": branch.branch_id,
                    "intent": branch.intent,
                    "text": branch.text,
                    "audio_path": _relative_cache_path(day_dir, branch.audio_path),
                    "patterns": list(branch.patterns),
                }
                for branch in mapping.branches
                if branch.audio_path is not None
            ],
        }


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid dialogue cache object: {key}")
    return value


def _str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing or invalid dialogue cache string: {key}")
    return value


def _int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Missing or invalid dialogue cache int: {key}")
    return value


def _patterns(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError("Dialogue cache patterns must be a list.")
    patterns: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            raise ValueError("Dialogue cache patterns must contain non-empty strings.")
        patterns.append(item)
    return tuple(patterns)


def _resolve_cache_path(day_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return day_dir / path


def _relative_cache_path(day_dir: Path, path: Path | None) -> str:
    if path is None:
        raise ValueError("Dialogue cache audio path is required.")
    try:
        return path.relative_to(day_dir).as_posix()
    except ValueError:
        return path.as_posix()
