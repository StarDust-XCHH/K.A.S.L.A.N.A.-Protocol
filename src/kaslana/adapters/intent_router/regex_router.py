"""Regex-based local intent router."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch, IntentMatch
from kaslana.ports.intent_router import IntentRouterPort

DEFAULT_PATTERNS: dict[str, tuple[str, ...]] = {
    "complaint": (
        r"再睡",
        r"赖床",
        r"不想起",
        r"困",
        r"累",
        r"五分钟",
        r"再.*分钟",
    ),
    "schedule_query": (
        r"安排",
        r"日程",
        r"计划",
        r"待办",
        r"几点",
        r"今天.*(什么|干嘛|做)",
        r"天气",
    ),
    "encouragement": (
        r"醒了",
        r"起来了",
        r"清醒",
        r"加油",
        r"开始",
        r"走吧",
    ),
}


class RegexIntentRouter(IntentRouterPort):
    """Match fixed morning-call intents without invoking a language model."""

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        default_patterns: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self._confidence_threshold = confidence_threshold
        self._default_patterns = default_patterns or DEFAULT_PATTERNS

    def match(self, transcript: str, mapping: CachedDialogueMapping) -> IntentMatch:
        normalized = transcript.strip()
        if not normalized:
            return IntentMatch(
                branch_id=None,
                confidence=0.0,
                matched=False,
                reason="empty_transcript",
            )

        for branch in mapping.branches:
            patterns = self._patterns_for_branch(branch)
            if not patterns:
                continue
            for pattern in patterns:
                if re.search(pattern, normalized, flags=re.IGNORECASE):
                    confidence = 1.0
                    return IntentMatch(
                        branch_id=branch.branch_id,
                        confidence=confidence,
                        matched=confidence >= self._confidence_threshold,
                        audio_path=branch.audio_path,
                        reason="regex_match",
                    )

        return IntentMatch(
            branch_id=None,
            confidence=0.0,
            matched=False,
            reason="no_regex_match",
        )

    def _patterns_for_branch(self, branch: DialogueBranch) -> tuple[str, ...]:
        if branch.patterns:
            return branch.patterns
        return tuple(
            self._default_patterns.get(branch.intent)
            or self._default_patterns.get(branch.branch_id)
            or ()
        )
