"""Rename-only flow as pure logic (no prompts, no printing).

The CLI (``tifo.pipeline.no_clustering``) and the Streamlit GUI both call these
functions. Anything interactive — previews, confirmations, progress bars —
lives in the frontend, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from tifo.naming.generator import generate_name
from tifo.naming.name_request import NameRequest, clean_stem, finalize
from tifo.naming.router import default_router
from tifo.naming.strategies import (
    ImageNameStrategy,
    LLMTextNameStrategy,
    name_batch,
)

_image_strategy = ImageNameStrategy()
_llm_strategy = LLMTextNameStrategy()


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


def _build_request(
    f: dict, formatter: Callable[[str], str], use_date: bool
) -> NameRequest:
    return NameRequest(
        original_file=f["file_name"],
        formatter=formatter,
        content=f.get("content"),
        file_type=f.get("file_type"),
        created_at=f.get("created_at"),
        use_date=use_date,
        metadata=f.get("metadata") or {},
    )


def _is_batchable(req: NameRequest) -> bool:
    """A file is batchable only if the LLM-text strategy would own it.

    Images are claimed first by the deterministic EXIF strategy, so they must
    NOT be batched (the router order is: image -> llm-text -> filename floor).
    Mirror that precedence here so batching never steals an image.
    """
    return not _image_strategy.can_handle(req) and _llm_strategy.can_handle(req)


def generate_new_names(
    raw_files: list[dict],
    formatter: Callable[[str], str],
    use_date: bool,
    *,
    describe: bool = True,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[str]:
    """Generate a new name for each file.

    ``describe=True`` derives names from file content (batched LLM + the
    deterministic strategies). ``describe=False`` is reformat-only: it just
    restyles the EXISTING filename through ``formatter`` (+ optional date),
    with no content read and no LLM call — milliseconds for any folder size.
    Output order matches ``raw_files``. ``on_progress(done, total)`` fires as
    files are finalized.
    """
    total = len(raw_files)

    # Reformat-only: pure string transform on the existing stem. No LLM.
    if not describe:
        names: list[str] = []
        for i, f in enumerate(raw_files):
            req = _build_request(f, formatter, use_date)
            names.append(finalize(clean_stem(f["file_name"]), req))
            if on_progress is not None:
                on_progress(i + 1, total)
        return names

    reqs = [_build_request(f, formatter, use_date) for f in raw_files]

    # Partition indices: LLM-batchable vs. deterministic (router handles those).
    batch_idx = [i for i, r in enumerate(reqs) if _is_batchable(r)]

    # One (chunked) batch call for all LLM-text files. Keyed by index-in-subset.
    # Report progress per chunk so the bar advances during the long LLM phase
    # instead of sitting at zero until every chunk is done. The batched files
    # are counted here; the loop below only advances for the remaining
    # (deterministic / fallback) files, so the count is monotonic.
    batched_names: dict[int, str] = {}
    n_batched = len(batch_idx)
    if batch_idx:
        sub_reqs = [reqs[i] for i in batch_idx]

        def _on_chunk(n_done: int) -> None:
            if on_progress is not None:
                on_progress(min(n_done, total), total)

        sub_result = name_batch(sub_reqs, on_chunk=_on_chunk)  # {pos_in_sub: name}
        batched_names = {batch_idx[pos]: name for pos, name in sub_result.items()}

    new_names: list[str] = []
    done = n_batched  # batched files already reported above
    for i, f in enumerate(raw_files):
        if i in batched_names:
            new_name = batched_names[i]
            new_names.append(new_name)
            continue  # already counted; don't double-report

        # Deterministic file, or a batch miss -> single-file naming.
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
        done += 1
        if on_progress is not None:
            on_progress(min(done, total), total)

    return new_names


def plan_renames(
    *,
    formatter: Callable[[str], str],
    use_date: bool,
    raw_files: list[dict],
    describe: bool = True,
    on_progress: Callable[[int, int], None] | None = None,
) -> RenamePlan:
    """Build the old→new name mapping without touching the filesystem.

    ``describe=False`` reformats existing names only (no content, no LLM).
    """
    old_names = [f["file_name"] for f in raw_files]
    new_names = generate_new_names(
        raw_files, formatter, use_date, describe=describe, on_progress=on_progress
    )
    return RenamePlan(old_names=old_names, new_names=new_names, raw_files=raw_files)


def apply_renames(plan: RenamePlan) -> RenameOutcome:
    """Perform the in-place rename described by ``plan`` (destructive)."""
    # Imported lazily so the module graph stays free of filesystem side effects
    # until a frontend actually commits.
    from tifo.renaming.renamer import rename_flow

    renamed, skipped, failed = rename_flow(plan.raw_files, plan.new_names)
    return RenameOutcome(renamed=renamed, skipped=skipped, failed=failed)
