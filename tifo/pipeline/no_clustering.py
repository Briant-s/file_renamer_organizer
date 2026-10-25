from rich.progress import Progress

from tifo.ui.display.preview import compare_results
from tifo.renaming.renamer import show_rename_results
from tifo.ui.prompts.rename import prompt_rename_option

from tifo.core.rename_service import (
    RenamePlan,
    apply_renames,
    generate_new_names,
)


def get_old_names(raw_files: list[dict]) -> list[str]:
    return [f["file_name"] for f in raw_files]


def get_new_names(raw_files: list[dict], formatter: callable, use_date: bool) -> list[str]:
    """CLI name generation: pure core logic + a rich progress bar.

    The core owns the LLM loop (``generate_new_names``); this wrapper only
    renders progress via the core's ``on_progress`` hook, keeping all
    presentation in the CLI layer.
    """
    with Progress() as progress:
        task = progress.add_task("Generating file names...", total=len(raw_files))

        def _advance(done: int, total: int) -> None:
            progress.update(task, completed=done)

        return generate_new_names(
            raw_files, formatter, use_date, on_progress=_advance
        )


def renaming_pipeline(*, formatter: callable, use_date: bool, raw_files: list[dict], root_dir: str):
    # Build the rename plan (generates new names with a progress bar).
    plan = RenamePlan(
        old_names=get_old_names(raw_files),
        new_names=get_new_names(raw_files, formatter, use_date),
        raw_files=raw_files,
    )

    # Preview old vs new, then confirm.
    compare_results(plan.old_names, plan.new_names)
    user_actions = prompt_rename_option(is_folder=False)

    if user_actions == "cancel":
        print("No changes were made.")
        return
    elif user_actions == "accept":
        outcome = apply_renames(plan)
        show_rename_results(
            outcome.renamed, outcome.skipped, outcome.failed, dest_root=root_dir
        )
        return
    elif user_actions == "manual":
        pass
