"""Naming request context + shared helpers.

`NameRequest` is the single input object passed to every naming strategy. Adding
a new signal later (audio tags, OCR text, etc.) means adding a field here — no
strategy signature changes. This is what keeps the router extensible without
rewrites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class NameRequest:
    """Everything a strategy might need to name one file.

    Kept as a plain, picklable dataclass (no open file handles, no live models)
    so requests can be dispatched to worker processes later for parallel naming.
    """

    original_file: str                      # file name, e.g. "DSC_4115.acr_.jpeg"
    formatter: Callable[[str], str]          # naming-style formatter (Title Case, etc.)
    content: str | None = None               # extracted text, if any
    file_type: str | None = None             # suffix, e.g. ".jpeg"
    created_at: datetime | None = None       # filesystem ctime, for date fallback
    use_date: bool = False                   # user chose a dated naming format
    metadata: dict[str, Any] = field(default_factory=dict)  # EXIF, archive members, ...

    @property
    def suffix(self) -> str:
        return Path(self.original_file).suffix

    @property
    def ext(self) -> str:
        """Normalized extension for routing: prefers file_type, falls back to suffix."""
        return (self.file_type or self.suffix).lower()


def clean_stem(original_file: str) -> str:
    """Human-readable version of the filename stem — the universal naming floor.

    'DSC_4115.acr_.jpeg' -> 'DSC 4115 acr'
    """
    stem = Path(original_file).stem
    stem = stem.replace(".", " ")  # flatten inner '.acr_' style compound stems
    cleaned = " ".join(stem.replace("_", " ").replace("-", " ").split())
    return cleaned or "untitled"


def resolve_date(explicit_date: str | None, created_at: datetime | None) -> str:
    """Date-prefix resolution, shared by all strategies.

    Priority: explicit (from content/EXIF) -> filesystem created_at -> today.
    """
    if explicit_date:
        return explicit_date
    if created_at:
        return created_at.strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")


def finalize(topic: str, req: NameRequest, *, explicit_date: str | None = None) -> str:
    """Apply the user's formatter + optional date prefix + original extension.

    Centralizes the final assembly so every strategy produces consistent output
    and no strategy has to re-implement date prefixing or extension handling.
    """
    formatted = req.formatter(topic.strip() or clean_stem(req.original_file))
    if req.use_date:
        date_str = resolve_date(explicit_date, req.created_at)
        return f"{date_str} {formatted}{req.suffix}"
    return f"{formatted}{req.suffix}"
