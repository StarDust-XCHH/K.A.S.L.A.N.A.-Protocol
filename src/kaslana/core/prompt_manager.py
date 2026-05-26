"""Load persona YAML and build scene-specific system prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

PromptScene = Literal["wake_call", "long_text_tts"]
LengthTier = Literal["short", "medium", "long", "stress"]
ToneStrength = Literal["low", "normal", "high"]

LENGTH_TIERS: dict[LengthTier, tuple[int, int]] = {
    "short": (80, 150),
    "medium": (300, 500),
    "long": (700, 1000),
    "stress": (1200, 1800),
}

TONE_LABELS: dict[ToneStrength, str] = {
    "low": "语气偏克制、自然",
    "normal": "语气元气、亲近、活泼",
    "high": "语气更活泼、更亲近，略带撒娇和鼓励感",
}


class PromptConfigError(ValueError):
    """Raised when persona YAML is missing required fields."""


@dataclass(frozen=True)
class TargetLength:
    min_chars: int
    max_chars: int


@dataclass(frozen=True)
class PersonaConfig:
    name: str
    franchise: str
    character: str
    locale: str
    safety_note: str


@dataclass(frozen=True)
class SceneConfig:
    style: str
    instructions: tuple[str, ...]
    max_sentences: int | None = None
    target_length: TargetLength | None = None


@dataclass(frozen=True)
class KianaPromptConfig:
    persona: PersonaConfig
    scenes: dict[str, SceneConfig]


class PromptManager:
    """Build system prompts for Kiana persona scenes."""

    def __init__(self, config: KianaPromptConfig) -> None:
        self._config = config

    @classmethod
    def from_yaml(cls, path: str | Path) -> PromptManager:
        return cls(load_kiana_prompt_config(path))

    def resolve_length_tier(self, length_tier: str | None) -> LengthTier:
        normalized = (length_tier or "long").strip().lower()
        if normalized not in LENGTH_TIERS:
            raise PromptConfigError(f"Invalid length tier: {length_tier!r}")
        return normalized  # type: ignore[return-value]

    def resolve_tone_strength(self, tone_strength: str | None) -> ToneStrength:
        normalized = (tone_strength or "normal").strip().lower()
        if normalized not in TONE_LABELS:
            raise PromptConfigError(f"Invalid tone strength: {tone_strength!r}")
        return normalized  # type: ignore[return-value]

    def build_system_prompt(
        self,
        scene: PromptScene,
        *,
        length_tier: LengthTier = "long",
    ) -> str:
        scene_config = self._require_scene(scene)
        persona = self._config.persona

        if scene == "wake_call":
            return self._build_wake_call_prompt(persona, scene_config)

        min_chars, max_chars = LENGTH_TIERS[length_tier]
        return self._build_long_text_prompt(persona, scene_config, min_chars, max_chars)

    def build_user_message(
        self,
        *,
        topic: str,
        scene: str = "",
        length_tier: LengthTier = "long",
        tone_strength: ToneStrength = "normal",
        user_hint: str = "",
    ) -> str:
        min_chars, max_chars = LENGTH_TIERS[length_tier]
        tone_label = TONE_LABELS[tone_strength]

        parts = [
            f"主题：{topic.strip()}",
            (
                "请用琪亚娜的口吻写一段适合朗读的中文对话式口语文本，"
                f"字数大约在 {min_chars} 到 {max_chars} 字之间。"
            ),
            "只输出可直接念给听众听的台词，不要括号旁白、心理描写或动作描写。",
            "若有偏向外国人的专名（如 Kaslana、Captain），可直接用英文拼写，便于语音合成。",
            f"语气强度：{tone_label}。",
            "请使用自然分句，不要使用 Markdown、编号列表或表格。",
        ]
        scene_text = scene.strip()
        if scene_text:
            parts.append(f"场景：{scene_text}")
        hint = user_hint.strip()
        if hint:
            parts.append(f"补充要求：{hint}")
        return "\n".join(parts)

    def _require_scene(self, scene: str) -> SceneConfig:
        scene_config = self._config.scenes.get(scene)
        if scene_config is None:
            raise PromptConfigError(f"Missing scene in persona config: {scene}")
        return scene_config

    @staticmethod
    def _build_wake_call_prompt(persona: PersonaConfig, scene: SceneConfig) -> str:
        max_sentences = scene.max_sentences or 3
        lines = [
            f"你是 {persona.franchise} 中的角色 {persona.character}（{persona.name}）。",
            f"语气：{scene.style}。",
            f"请用 {persona.locale} 回复，最多 {max_sentences} 句。",
            persona.safety_note,
        ]
        lines.extend(scene.instructions)
        return "\n".join(lines)

    @staticmethod
    def _build_long_text_prompt(
        persona: PersonaConfig,
        scene: SceneConfig,
        min_chars: int,
        max_chars: int,
    ) -> str:
        lines = [
            f"你是 {persona.franchise} 中的角色 {persona.character}（{persona.name}）。",
            scene.style,
            "请模仿该角色在作品中的口吻与性格进行角色扮演式创作。",
            f"输出语言：{persona.locale}。",
            f"目标长度：约 {min_chars} 到 {max_chars} 个汉字（允许略有浮动）。",
            persona.safety_note,
        ]
        lines.extend(scene.instructions)
        return "\n".join(lines)


def load_kiana_prompt_config(path: str | Path) -> KianaPromptConfig:
    resolved = Path(path)
    if not resolved.exists():
        raise PromptConfigError(f"Persona file not found: {resolved}")

    with resolved.open("r", encoding="utf-8") as stream:
        raw: Any = yaml.safe_load(stream)

    if not isinstance(raw, dict):
        raise PromptConfigError(f"Persona file must be a YAML mapping: {resolved}")

    persona_raw = _mapping(raw, "persona")
    scenes_raw = _mapping(raw, "scenes")

    persona = PersonaConfig(
        name=_str(persona_raw, "name"),
        franchise=_str(persona_raw, "franchise"),
        character=_str(persona_raw, "character"),
        locale=_str(persona_raw, "locale"),
        safety_note=_str(persona_raw, "safety_note"),
    )

    scenes: dict[str, SceneConfig] = {}
    for scene_name, scene_value in scenes_raw.items():
        if not isinstance(scene_value, dict):
            raise PromptConfigError(f"Scene {scene_name!r} must be a mapping")
        target_length = None
        if "target_length" in scene_value:
            length_raw = _mapping(scene_value, "target_length")
            target_length = TargetLength(
                min_chars=_int(length_raw, "min_chars"),
                max_chars=_int(length_raw, "max_chars"),
            )
        scenes[str(scene_name)] = SceneConfig(
            style=_str(scene_value, "style"),
            instructions=tuple(_str_list(scene_value, "instructions")),
            max_sentences=_optional_int(scene_value, "max_sentences"),
            target_length=target_length,
        )

    for required in ("wake_call", "long_text_tts"):
        if required not in scenes:
            raise PromptConfigError(f"Missing required scene: {required}")

    return KianaPromptConfig(persona=persona, scenes=scenes)


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise PromptConfigError(f"Missing or invalid mapping: {key}")
    return value


def _str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PromptConfigError(f"Missing or invalid string field: {key}")
    return value.strip()


def _str_list(raw: dict[str, Any], key: str) -> list[str]:
    value = raw.get(key)
    if not isinstance(value, list) or not value:
        raise PromptConfigError(f"Missing or invalid list field: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise PromptConfigError(f"Invalid list item in {key}")
        items.append(item.strip())
    return items


def _int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or value <= 0:
        raise PromptConfigError(f"Missing or invalid integer field: {key}")
    return value


def _optional_int(raw: dict[str, Any], key: str) -> int | None:
    if key not in raw:
        return None
    return _int(raw, key)
