"""Rename-only flow as pure logic (no prompts, no printing).

The CLI (``tifo.pipeline.no_clustering``) and the Streamlit GUI both call these
functions. Anything interactive — previews, confirmations, progress bars —
lives in the frontend, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from tifo.naming.generator import generate_name


@dataclass
class RenamePlan:
    """Everything a frontend needs to preview and then apply a rename.

    ``raw_files`` is carried through unchanged so :func:`apply_renames` can act
    on the exact same file dicts the plan was built from.
    """

    old_names: list[str]
    new_names: list[str]
    raw_files: list[dict] = field(repr=False)


@dataclass
class RenameOutcome:
    """Result of applying a rename plan. Lists of ``(old_name, detail)``."""

    renamed: list[tuple[str, str]]
    skipped: list[tuple[str, str]]
    failed: list[tuple[str, str]]


def generate_new_names(
    raw_files: list[dict],
    formatter: Callable[[str], str],
    use_date: bool,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[str]:
    """Generate a new name for each file via the local LLM.

    ``on_progress(done, total)`` is an optional hook so a frontend can render a
    progress bar (rich ``track`` for the CLI, ``st.progress`` for the GUI)
    without this function depending on either library.
    """
    new_names: list[str] = []
    total = len(raw_files)

    for index, f in enumerate(raw_files):
        new_name = generate_name(
            f["content"],
            f["file_name"],
            formatter,
            f["created_at"],
            use_date,
            file_type=f.get("file_type"),
            metadata=f.get("metadata"),
        )
        new_names.append(new_name)
        if on_progress is not None:
            on_progress(index + 1, total)

    return new_names


def plan_renames(
    *,
    formatter: Callable[[str], str],
    use_date: bool,
    raw_files: list[dict],
    on_progress: Callable[[int, int], None] | None = None,
) -> RenamePlan:
    """Build the old→new name mapping without touching the filesystem."""
    old_names = [f["file_name"] for f in raw_files]
    new_names = generate_new_names(
        raw_files, formatter, use_date, on_progress=on_progress
    )
    return RenamePlan(old_names=old_names, new_names=new_names, raw_files=raw_files)


def apply_renames(plan: RenamePlan) -> RenameOutcome:
    """Perform the in-place rename described by ``plan`` (destructive)."""
    # Imported lazily so the module graph stays free of filesystem side effects
    # until a frontend actually commits.
    from tifo.renaming.renamer import rename_flow

    renamed, skipped, failed = rename_flow(plan.raw_files, plan.new_names)
    return RenameOutcome(renamed=renamed, skipped=skipped, failed=failed)
