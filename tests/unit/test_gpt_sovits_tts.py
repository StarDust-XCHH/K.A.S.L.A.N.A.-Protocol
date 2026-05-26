from __future__ import annotations

import json
import wave
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from kaslana.adapters.tts.gpt_sovits import (
    GptSovitsError,
    GptSovitsTts,
    list_infer_config_emotions,
    load_voice_profile_from_infer_config,
    normalize_tts_text,
)


def test_load_voice_profile_from_infer_config_resolves_paths(tmp_path: Path) -> None:
    model_dir = tmp_path / "kiana"
    ref_dir = model_dir / "refer_audio"
    ref_dir.mkdir(parents=True)
    ref_path = ref_dir / "default.wav"
    ref_path.write_bytes(_wav_bytes())

    infer_config = model_dir / "infer_config.json"
    infer_config.write_text(
        json.dumps(
            {
                "gpt_path": "kiana.ckpt",
                "sovits_path": "kiana.pth",
                "emotion_list": {
                    "default": {
                        "ref_wav_path": "refer_audio/default.wav",
                        "prompt_text": "让我猜猜看。",
                        "prompt_language": "中文",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    profile = load_voice_profile_from_infer_config(infer_config)

    assert profile.root_dir == model_dir.resolve()
    assert profile.reference_audio_path == ref_path.resolve()
    assert profile.prompt_text == "让我猜猜看。"
    assert profile.prompt_language == "zh"
    assert profile.gpt_path == (model_dir / "kiana.ckpt").resolve()
    assert profile.sovits_path == (model_dir / "kiana.pth").resolve()


def test_list_infer_config_emotions_returns_sorted_keys(tmp_path: Path) -> None:
    infer_config = tmp_path / "infer_config.json"
    infer_config.write_text(
        json.dumps({"emotion_list": {"z": {}, "default": {}, "a": {}}}),
        encoding="utf-8",
    )

    assert list_infer_config_emotions(infer_config) == ("a", "default", "z")


@pytest.mark.asyncio
async def test_synthesize_posts_expected_gpt_sovits_payload(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)
    profile = load_voice_profile_from_infer_config(infer_config)
    tts = FakeGptSovitsTts(voice_profile=profile)

    audio = await tts.synthesize("  早安，舰长。\n- 该起床啦。 ")

    assert audio.sample_rate == 16000
    assert audio.channels == 1
    assert audio.format == "wav"
    assert tts.posts[0][0] == "tts"
    payload = tts.posts[0][1]
    assert payload["text"] == "早安，舰长。 该起床啦。"
    assert payload["text_lang"] == "zh"
    assert payload["prompt_lang"] == "zh"
    assert payload["prompt_text"] == "让我猜猜看。"
    assert payload["ref_audio_path"] == str((tmp_path / "refer.wav").resolve())


@pytest.mark.asyncio
async def test_synthesize_can_build_gsvi_payload(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)
    profile = load_voice_profile_from_infer_config(infer_config)
    tts = FakeGptSovitsTts(
        voice_profile=profile,
        api_style="gsvi",
        character="琪亚娜E7",
        emotion="default",
    )

    audio = await tts.synthesize("早安。")

    assert audio.sample_rate == 16000
    payload = tts.posts[0][1]
    assert payload["text"] == "早安。"
    assert payload["text_language"] == "zh"
    assert payload["character"] == "琪亚娜E7"
    assert payload["cha_name"] == "琪亚娜E7"
    assert payload["emotion"] == "default"
    assert payload["character_emotion"] == "default"
    assert payload["format"] == "wav"


@pytest.mark.asyncio
async def test_load_weights_calls_weight_switch_endpoints(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)
    profile = load_voice_profile_from_infer_config(infer_config)
    tts = FakeGptSovitsTts(voice_profile=profile)

    await tts.load_weights()

    assert tts.gets == [
        ("set_gpt_weights", {"weights_path": str((tmp_path / "kiana.ckpt").resolve())}),
        ("set_sovits_weights", {"weights_path": str((tmp_path / "kiana.pth").resolve())}),
    ]


@pytest.mark.asyncio
async def test_load_weights_is_noop_for_gsvi_style(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)
    profile = load_voice_profile_from_infer_config(infer_config)
    tts = FakeGptSovitsTts(voice_profile=profile, api_style="gsvi")

    await tts.load_weights()

    assert tts.gets == []


@pytest.mark.asyncio
async def test_synthesize_rejects_empty_text(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)
    profile = load_voice_profile_from_infer_config(infer_config)
    tts = FakeGptSovitsTts(voice_profile=profile)

    with pytest.raises(GptSovitsError, match="empty"):
        await tts.synthesize("```python\nprint('skip')\n```")


def test_unknown_emotion_mentions_available_keys(tmp_path: Path) -> None:
    infer_config = _write_minimal_infer_config(tmp_path)

    with pytest.raises(GptSovitsError, match="Available emotions: default"):
        load_voice_profile_from_infer_config(infer_config, emotion="angry")


def test_normalize_tts_text_removes_markdown_noise() -> None:
    text = """
1. 早安，舰长。
- 该起床啦。
```json
{"skip": true}
```
`今天`也要元气满满。
"""

    assert normalize_tts_text(text) == "早安，舰长。 该起床啦。 今天也要元气满满。"


class FakeGptSovitsTts(GptSovitsTts):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.posts: list[tuple[str, dict[str, Any]]] = []
        self.gets: list[tuple[str, dict[str, str]]] = []

    def _post_json(self, route: str, payload: dict[str, Any]) -> bytes:
        self.posts.append((route, payload))
        return _wav_bytes()

    def _get_query(self, route: str, params: dict[str, str]) -> bytes:
        self.gets.append((route, params))
        return b"ok"


def _write_minimal_infer_config(tmp_path: Path) -> Path:
    (tmp_path / "refer.wav").write_bytes(_wav_bytes())
    infer_config = tmp_path / "infer_config.json"
    infer_config.write_text(
        json.dumps(
            {
                "gpt_path": "kiana.ckpt",
                "sovits_path": "kiana.pth",
                "emotion_list": {
                    "default": {
                        "ref_wav_path": "refer.wav",
                        "prompt_text": "让我猜猜看。",
                        "prompt_language": "中文",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return infer_config


def _wav_bytes() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()
