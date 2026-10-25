"""Rename + folder-organization flow as pure logic (no prompts, no printing).

Mirrors :mod:`tifo.core.rename_service` for the clustering workflow. The
classifier assigns each file a ``matching_folder``; the frontend previews the
folder tree and confirms; then :func:`apply_organization` moves (and optionally
renames) every file into place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from tifo.classifiers import CLASSIFIERS
from tifo.core.rename_service import RenameOutcome, generate_new_names


def embedding_prep(raw_data_list: list[dict]) -> list[dict]:
    """Project raw extraction dicts down to the fields the classifiers use."""
    return [
        {
            "path": item["path"],
            "file_name": item["file_name"],
            "stem": item.get("stem", item["file_name"]),
            "file_type": item.get("file_type", ""),
            "content": item["content"],
            "created_at": item.get("created_at"),
            "metadata": item.get("metadata", {}),
        }
        for item in raw_data_list
    ]


@dataclass
class OrganizePlan:
    """Classification result plus the context needed to apply the move.

    ``results`` carries ``matching_folder`` per file. Build the folder-tree
    preview by grouping ``results`` on that key.
    """

    results: list[dict] = field(repr=False)
    root_dir: str


def plan_organization(
    *,
    strat_choice: str,
    raw_files: list[dict],
    folder_labels: list[str] | None,
    embedder,
    root_dir: str,
) -> OrganizePlan:
    """Classify files into folders without touching the filesystem.

    ``embedder`` is only required for the ``manual`` strategy; pass ``None`` for
    ``file_based``. ``folder_labels`` likewise applies to ``manual`` only.
    """
    pre_embed = embedding_prep(raw_files)

    cls = CLASSIFIERS[strat_choice]
    if strat_choice == "manual":
        classifier = cls(model=embedder, folder_labels=folder_labels)
    else:
        classifier = cls()

    results = classifier.classify(pre_embed=pre_embed)
    return OrganizePlan(results=results, root_dir=root_dir)


def resolve_target_names(
    plan: OrganizePlan,
    *,
    rename_too: bool,
    formatter: Callable[[str], str] | None = None,
    use_date: bool = False,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[str]:
    """Decide the stem each file gets once moved.

    ``rename_too=False`` keeps the original stems (move-only, no LLM calls).
    ``rename_too=True`` generates fresh names and therefore needs ``formatter``.
    """
    if not rename_too:
        return [f["stem"] for f in plan.results]

    if formatter is None:
        raise ValueError("formatter is required when rename_too=True")

    return generate_new_names(
        plan.results, formatter, use_date, on_progress=on_progress
    )


def apply_organization(plan: OrganizePlan, new_names: list[str]) -> RenameOutcome:
    """Move (and optionally rename) every file into its folder (destructive)."""
    from tifo.renaming.renamer import move_flow

    renamed, skipped, failed = move_flow(
        plan.results, new_names, base_dir=plan.root_dir
    )
    return RenameOutcome(renamed=renamed, skipped=skipped, failed=failed)
