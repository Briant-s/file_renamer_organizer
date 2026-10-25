from rich.console import Console

from tifo.pipeline.confirmation import preview_folders
from tifo.pipeline.no_clustering import get_new_names

from tifo.renaming.renamer import show_rename_results
from tifo.naming.formats import prompt_naming_format
from tifo.ui.prompts.rename import prompt_rename_option, prompt_rename_or_move
from tifo.ui.prompts.folders import get_folder_names

from tifo.core.organize_service import (
    apply_organization,
    plan_organization,
)

console = Console()


def with_clustering_pipeline(*, strat_choice, raw_files, folder_labels, res, root_dir) -> None:
    # 1-3. Classify files into folders (pure core logic).
    plan = plan_organization(
        strat_choice=strat_choice,
        raw_files=raw_files,
        folder_labels=folder_labels,
        embedder=res.embedder,
        root_dir=root_dir,
    )

    # 4. Preview tree
    preview_folders(matching_results=plan.results)

    # 5. Ask folder confirmation
    user_actions = prompt_rename_option(is_folder=True)

    if user_actions == "cancel":
        console.print("No changes were made.")
        return
    elif user_actions == "manual":
        # Interactive per-file editing not implemented yet.
        console.print("[yellow]Individual edit not implemented yet.[/yellow]")
        return

    # 6. Decide whether to also rename, or just move under original names.
    rename_too = prompt_rename_or_move()
    if rename_too:
        # Only prompt for a naming format when the user actually wants renames.
        label, formatter = prompt_naming_format()
        use_date = "YYYY-MM-DD" in label
        new_names = get_new_names(plan.results, formatter, use_date)
    else:
        new_names = [f["stem"] for f in plan.results]

    # 7. Move (and optionally rename) each file into its matching_folder.
    outcome = apply_organization(plan, new_names)
    show_rename_results(
        outcome.renamed, outcome.skipped, outcome.failed, dest_root=root_dir
    )
