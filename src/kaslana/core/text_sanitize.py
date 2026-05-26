"""Shared text cleanup for dialogue TTS and LLM output."""

from __future__ import annotations

import re

_PAREN_FULL = re.compile(r"（[^（）]*）")
_PAREN_HALF = re.compile(r"\([^()]*\)")


def strip_parenthetical_asides(text: str) -> str:
    """Remove parenthetical asides such as inner monologue or stage directions."""

    cleaned = text
    while True:
        updated = _PAREN_FULL.sub("", cleaned)
        updated = _PAREN_HALF.sub("", updated)
        if updated == cleaned:
            break
        cleaned = updated
    return cleaned
