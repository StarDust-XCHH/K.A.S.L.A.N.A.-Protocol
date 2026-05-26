from __future__ import annotations

from pathlib import Path

import pytest

from kaslana.config.loader import load_config
from kaslana.config.schema import ConfigError


def test_example_config_loads() -> None:
    config = load_config(Path("config/config.example.yaml"))

    assert config.project.name == "K.A.S.L.A.N.A. Protocol"
    assert config.scheduler.wake_time == "07:30"
    assert config.automation.wechat.package_name == "com.tencent.mm"
    assert config.audio.sample_rate == 16000
    assert config.vad.provider == "silero"
    assert config.llm.api_key_env == "TONGYI_API_KEY"
    assert config.llm.model == "qwen-flash"
    assert config.offline_cache.enabled is False
    assert config.offline_cache.cache_dir == Path("cache")
    assert config.ingestion.paths == ()
    assert config.intent_matching.provider == "regex"
    assert config.batch_preprocess.schedule_time == "03:00"


def test_missing_required_mapping_raises_config_error(tmp_path: Path) -> None:
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text(
        """
project:
  name: Broken
  timezone: UTC
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="scheduler"):
        load_config(bad_config)
