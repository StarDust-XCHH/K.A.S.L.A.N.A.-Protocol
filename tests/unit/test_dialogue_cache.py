from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from kaslana.adapters.dialogue_cache import JsonDialogueCache
from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch


@pytest.mark.asyncio
async def test_json_dialogue_cache_saves_and_loads_mapping(tmp_path: Path) -> None:
    target_date = date(2026, 5, 25)
    day_dir = tmp_path / target_date.isoformat()
    greeting = day_dir / "greeting.wav"
    branch_audio = day_dir / "complaint.wav"
    mapping = CachedDialogueMapping(
        target_date=target_date,
        greeting_text="早安。",
        greeting_audio_path=greeting,
        branches=(
            DialogueBranch(
                branch_id="complaint",
                intent="complaint",
                text="不许赖床。",
                audio_path=branch_audio,
                patterns=(r"再睡",),
            ),
        ),
    )

    cache = JsonDialogueCache(tmp_path)
    await cache.save_mapping(mapping)
    loaded = await cache.load_mapping(target_date)

    assert loaded is not None
    assert loaded.greeting_audio_path == greeting
    assert loaded.branches[0].audio_path == branch_audio
    assert loaded.branches[0].patterns == (r"再睡",)


@pytest.mark.asyncio
async def test_json_dialogue_cache_returns_none_when_absent(tmp_path: Path) -> None:
    loaded = await JsonDialogueCache(tmp_path).load_mapping(date(2026, 5, 25))

    assert loaded is None


@pytest.mark.asyncio
async def test_json_dialogue_cache_rejects_broken_json(tmp_path: Path) -> None:
    target_date = date(2026, 5, 25)
    day_dir = tmp_path / target_date.isoformat()
    day_dir.mkdir(parents=True)
    (day_dir / "state_mapping.json").write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid dialogue cache JSON"):
        await JsonDialogueCache(tmp_path).load_mapping(target_date)
