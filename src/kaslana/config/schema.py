"""Typed configuration schema for K.A.S.L.A.N.A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a configuration file is missing or invalid."""


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    timezone: str


@dataclass(frozen=True)
class SchedulerConfig:
    enabled: bool
    wake_time: str


@dataclass(frozen=True)
class WechatConfig:
    package_name: str
    target_contact_alias: str
    launch_timeout_s: float


@dataclass(frozen=True)
class AutomationConfig:
    android_device_id: str
    wechat: WechatConfig
    coordinates: dict[str, Point]


@dataclass(frozen=True)
class AudioConfig:
    input_device: str | int
    output_device: str | int
    sample_rate: int
    channels: int
    chunk_ms: int
    greeting_path: Path


@dataclass(frozen=True)
class VadConfig:
    provider: str
    threshold: float
    min_speech_ms: int
    silence_ms: int
    max_utterance_s: float


@dataclass(frozen=True)
class AsrConfig:
    provider: str
    model: str
    language: str


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    base_url: str
    model: str
    api_key_env: str
    timeout_s: float


@dataclass(frozen=True)
class TtsConfig:
    provider: str
    endpoint: str
    speaker: str
    timeout_s: float


@dataclass(frozen=True)
class PromptConfig:
    persona_path: Path


@dataclass(frozen=True)
class AppConfig:
    project: ProjectConfig
    scheduler: SchedulerConfig
    automation: AutomationConfig
    audio: AudioConfig
    vad: VadConfig
    asr: AsrConfig
    llm: LlmConfig
    tts: TtsConfig
    prompts: PromptConfig

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> AppConfig:
        project = _mapping(raw, "project")
        scheduler = _mapping(raw, "scheduler")
        automation = _mapping(raw, "automation")
        wechat = _mapping(automation, "wechat")
        audio = _mapping(raw, "audio")
        vad = _mapping(raw, "vad")
        asr = _mapping(raw, "asr")
        llm = _mapping(raw, "llm")
        tts = _mapping(raw, "tts")
        prompts = _mapping(raw, "prompts")

        return cls(
            project=ProjectConfig(
                name=_str(project, "name"),
                timezone=_str(project, "timezone"),
            ),
            scheduler=SchedulerConfig(
                enabled=_bool(scheduler, "enabled"),
                wake_time=_str(scheduler, "wake_time"),
            ),
            automation=AutomationConfig(
                android_device_id=_str(automation, "android_device_id"),
                wechat=WechatConfig(
                    package_name=_str(wechat, "package_name"),
                    target_contact_alias=_str(wechat, "target_contact_alias"),
                    launch_timeout_s=_float(wechat, "launch_timeout_s"),
                ),
                coordinates=_points(_mapping(automation, "coordinates"), "automation.coordinates"),
            ),
            audio=AudioConfig(
                input_device=_str_or_int(audio, "input_device"),
                output_device=_str_or_int(audio, "output_device"),
                sample_rate=_int(audio, "sample_rate"),
                channels=_int(audio, "channels"),
                chunk_ms=_int(audio, "chunk_ms"),
                greeting_path=Path(_str(audio, "greeting_path")),
            ),
            vad=VadConfig(
                provider=_str(vad, "provider"),
                threshold=_float(vad, "threshold"),
                min_speech_ms=_int(vad, "min_speech_ms"),
                silence_ms=_int(vad, "silence_ms"),
                max_utterance_s=_float(vad, "max_utterance_s"),
            ),
            asr=AsrConfig(
                provider=_str(asr, "provider"),
                model=_str(asr, "model"),
                language=_str(asr, "language"),
            ),
            llm=LlmConfig(
                provider=_str(llm, "provider"),
                base_url=_str(llm, "base_url"),
                model=_str(llm, "model"),
                api_key_env=_str(llm, "api_key_env"),
                timeout_s=_float(llm, "timeout_s"),
            ),
            tts=TtsConfig(
                provider=_str(tts, "provider"),
                endpoint=_str(tts, "endpoint"),
                speaker=_str(tts, "speaker"),
                timeout_s=_float(tts, "timeout_s"),
            ),
            prompts=PromptConfig(
                persona_path=Path(_str(prompts, "persona_path")),
            ),
        )


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Missing or invalid mapping: {key}")
    return value


def _str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"Missing or invalid string: {key}")
    return value


def _str_or_int(raw: dict[str, Any], key: str) -> str | int:
    value = raw.get(key)
    if isinstance(value, str) and value:
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ConfigError(f"Missing or invalid string/int: {key}")


def _bool(raw: dict[str, Any], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"Missing or invalid bool: {key}")
    return value


def _int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"Missing or invalid int: {key}")
    return value


def _float(raw: dict[str, Any], key: str) -> float:
    value = raw.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ConfigError(f"Missing or invalid float: {key}")
    return float(value)


def _points(raw: dict[str, Any], path: str) -> dict[str, Point]:
    points: dict[str, Point] = {}
    for name, value in raw.items():
        if not isinstance(value, dict):
            raise ConfigError(f"Missing or invalid point: {path}.{name}")
        points[name] = Point(
            x=_int(value, "x"),
            y=_int(value, "y"),
        )
    return points
