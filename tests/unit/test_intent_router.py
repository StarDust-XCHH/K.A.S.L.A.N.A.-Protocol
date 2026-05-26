from __future__ import annotations

from datetime import date
from pathlib import Path

from kaslana.adapters.intent_router import RegexIntentRouter
from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch


def build_mapping() -> CachedDialogueMapping:
    return CachedDialogueMapping(
        target_date=date(2026, 5, 25),
        greeting_text="早安，该起床啦。",
        greeting_audio_path=Path("greeting.wav"),
        branches=(
            DialogueBranch(
                branch_id="complaint",
                intent="complaint",
                text="不许赖床。",
                audio_path=Path("complaint.wav"),
            ),
            DialogueBranch(
                branch_id="schedule_query",
                intent="schedule_query",
                text="今天有这些安排。",
                audio_path=Path("schedule.wav"),
            ),
            DialogueBranch(
                branch_id="encouragement",
                intent="encouragement",
                text="很好，开始吧。",
                audio_path=Path("encouragement.wav"),
            ),
        ),
    )


def test_regex_router_matches_morning_branches() -> None:
    router = RegexIntentRouter()
    mapping = build_mapping()

    assert router.match("让我再睡五分钟", mapping).branch_id == "complaint"
    assert router.match("今天有什么安排", mapping).branch_id == "schedule_query"
    assert router.match("我醒了，准备开始", mapping).branch_id == "encouragement"


def test_regex_router_returns_miss_for_unrelated_text() -> None:
    match = RegexIntentRouter().match("昨天那本书放在哪里", build_mapping())

    assert match.matched is False
    assert match.branch_id is None
    assert match.reason == "no_regex_match"
