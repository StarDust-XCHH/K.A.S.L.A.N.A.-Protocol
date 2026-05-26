"""Nightly offline dialogue prediction and audio pre-rendering skeleton."""

from __future__ import annotations

import json
import wave
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch, DialogueStateTree
from kaslana.ports.dialogue_cache import DialogueCachePort
from kaslana.ports.ingestion import DataIngestionPort
from kaslana.ports.llm import ConversationTurn, LlmPort
from kaslana.ports.tts import TtsAudio, TtsPort
from kaslana.ports.weather import WeatherProviderPort


@dataclass(frozen=True)
class OfflinePreprocessOptions:
    target_date: date
    cache_dir: Path
    location: str
    system_prompt: str = ""


@dataclass(frozen=True)
class OfflinePreprocessorDependencies:
    ingestion: DataIngestionPort
    weather: WeatherProviderPort
    llm: LlmPort
    tts: TtsPort
    cache: DialogueCachePort


class OfflinePreprocessor:
    """Build a daily dialogue cache from local context and model ports."""

    def __init__(self, dependencies: OfflinePreprocessorDependencies) -> None:
        self._deps = dependencies

    async def run(self, options: OfflinePreprocessOptions) -> CachedDialogueMapping:
        items = await self._deps.ingestion.collect(options.target_date)
        weather = await self._deps.weather.get_weather(options.target_date, options.location)

        response = await self._deps.llm.complete(
            options.system_prompt,
            [
                ConversationTurn(
                    role="user",
                    content=_build_prediction_prompt(options.target_date, weather.summary, items),
                )
            ],
        )
        tree = _parse_dialogue_tree(
            response.text,
            target_date=options.target_date,
            source_count=len(items),
        )

        day_dir = options.cache_dir / options.target_date.isoformat()
        day_dir.mkdir(parents=True, exist_ok=True)

        greeting_audio = await self._deps.tts.synthesize(tree.greeting_text)
        greeting_audio_path = day_dir / "greeting.wav"
        _write_tts_audio(greeting_audio_path, greeting_audio)

        cached_branches: list[DialogueBranch] = []
        for branch in tree.branches:
            branch_audio = await self._deps.tts.synthesize(branch.text)
            branch_audio_path = day_dir / f"{branch.branch_id}.wav"
            _write_tts_audio(branch_audio_path, branch_audio)
            cached_branches.append(
                DialogueBranch(
                    branch_id=branch.branch_id,
                    intent=branch.intent,
                    text=branch.text,
                    audio_path=branch_audio_path,
                    patterns=branch.patterns,
                )
            )

        mapping = CachedDialogueMapping(
            target_date=options.target_date,
            greeting_text=tree.greeting_text,
            greeting_audio_path=greeting_audio_path,
            branches=tuple(cached_branches),
        )
        await self._deps.cache.save_mapping(mapping)
        return mapping


def _build_prediction_prompt(target_date: date, weather_summary: str, items: object) -> str:
    return "\n".join(
        [
            "Generate a JSON dialogue state tree for a morning wake-up call.",
            "Return only JSON with keys: greeting_text, branches.",
            "Each branch must include id, intent, text, and optional patterns.",
            f"Date: {target_date.isoformat()}",
            f"Weather: {weather_summary or 'unknown'}",
            f"Local context: {items}",
        ]
    )


def _parse_dialogue_tree(raw_text: str, target_date: date, source_count: int) -> DialogueStateTree:
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM prediction response must be JSON.") from exc

    if not isinstance(raw, dict):
        raise ValueError("LLM prediction JSON must be an object.")

    greeting_text = _str(raw, "greeting_text")
    raw_branches = raw.get("branches")
    if not isinstance(raw_branches, list):
        raise ValueError("LLM prediction JSON branches must be a list.")

    branches = tuple(
        DialogueBranch(
            branch_id=_str(branch, "id"),
            intent=_str(branch, "intent"),
            text=_str(branch, "text"),
            patterns=_patterns(branch.get("patterns", [])),
        )
        for branch in raw_branches
        if isinstance(branch, dict)
    )
    if len(branches) != len(raw_branches):
        raise ValueError("LLM prediction branches must contain only objects.")

    return DialogueStateTree(
        target_date=target_date,
        greeting_text=greeting_text,
        branches=branches,
        source_count=source_count,
    )


def _write_tts_audio(path: Path, audio: TtsAudio) -> None:
    if not audio.audio:
        raise ValueError("TTS returned empty audio.")
    if audio.format == "wav":
        path.write_bytes(audio.audio)
        return
    if audio.format != "pcm_s16le":
        raise ValueError(f"Unsupported TTS audio format for cache: {audio.format}")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(audio.channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(audio.sample_rate)
        wav_file.writeframes(audio.audio)


def _str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing or invalid prediction string: {key}")
    return value


def _patterns(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("Prediction patterns must be a list.")
    patterns: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            raise ValueError("Prediction patterns must contain non-empty strings.")
        patterns.append(item)
    return tuple(patterns)
