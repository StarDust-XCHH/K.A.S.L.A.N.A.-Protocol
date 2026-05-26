"""Local file ingestion adapter for offline prediction input."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path

from kaslana.domain.offline_cache import IngestedItem, IngestedItemKind
from kaslana.ports.ingestion import DataIngestionPort


class LocalFilesDataIngestion(DataIngestionPort):
    """Read user-selected Markdown, TXT, and JSON files as local context."""

    def __init__(self, paths: Sequence[Path | str] = ()) -> None:
        self._paths = tuple(Path(path) for path in paths)

    async def collect(self, target_date: date) -> Sequence[IngestedItem]:
        items: list[IngestedItem] = []
        for path in self._paths:
            if not path.exists() or not path.is_file():
                continue
            items.append(
                IngestedItem(
                    source=path,
                    content=path.read_text(encoding="utf-8"),
                    kind=_kind_for_path(path),
                    target_date=target_date,
                )
            )
        return tuple(items)


def _kind_for_path(path: Path) -> IngestedItemKind:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".json":
        return "json"
    return "text"
