from __future__ import annotations

import os
from pathlib import Path

import pytest

from kaslana.core.prompt_manager import LENGTH_TIERS, PromptConfigError, PromptManager


def test_long_text_prompt_mentions_honkai_kiana() -> None:
    manager = PromptManager.from_yaml(Path("config/prompts/kiana.yaml"))

    system_prompt = manager.build_system_prompt("long_text_tts", length_tier="long")

    assert "《崩坏三》" in system_prompt
    assert "琪亚娜" in system_prompt
    assert "Markdown" in system_prompt
    assert "官方琪亚娜本人" in system_prompt or "不要声称" in system_prompt


def test_long_text_prompt_mentions_foreign_name_guidance() -> None:
    manager = PromptManager.from_yaml(Path("config/prompts/kiana.yaml"))

    system_prompt = manager.build_system_prompt("long_text_tts", length_tier="short")
    user_message = manager.build_user_message(topic="早安", length_tier="short")

    assert "Kaslana" in system_prompt
    assert "Kaslana" in user_message


def test_length_tiers_map_to_expected_ranges() -> None:
    manager = PromptManager.from_yaml(Path("config/prompts/kiana.yaml"))

    user_message = manager.build_user_message(
        topic="测试",
        length_tier="stress",
        tone_strength="normal",
    )

    min_chars, max_chars = LENGTH_TIERS["stress"]
    assert str(min_chars) in user_message
    assert str(max_chars) in user_message


def test_build_user_message_includes_scene_and_tone() -> None:
    manager = PromptManager.from_yaml(Path("config/prompts/kiana.yaml"))

    user_message = manager.build_user_message(
        topic="早晨叫醒",
        scene="电话叫醒",
        user_hint="提到芽衣",
        length_tier="medium",
        tone_strength="high",
    )

    assert "早晨叫醒" in user_message
    assert "电话叫醒" in user_message
    assert "芽衣" in user_message
    assert "撒娇" in user_message


def test_missing_scene_raises(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "kiana.yaml"
    bad_yaml.write_text(
        """
persona:
  name: "琪亚娜"
  franchise: "《崩坏三》"
  character: "琪亚娜·卡斯兰娜"
  locale: "zh-CN"
  safety_note: "安全"
scenes:
  wake_call:
    style: "短"
    instructions:
      - "简短"
""",
        encoding="utf-8",
    )

    with pytest.raises(PromptConfigError, match="long_text_tts"):
        PromptManager.from_yaml(bad_yaml)


def test_prompt_does_not_embed_env_secrets() -> None:
    os.environ["TONGYI_API_KEY"] = "secret-test-key-do-not-log"
    try:
        manager = PromptManager.from_yaml(Path("config/prompts/kiana.yaml"))
        prompt = manager.build_system_prompt("long_text_tts")
        assert "secret-test-key" not in prompt
    finally:
        if os.environ.get("TONGYI_API_KEY") == "secret-test-key-do-not-log":
            del os.environ["TONGYI_API_KEY"]
