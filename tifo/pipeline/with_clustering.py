import questionary
from rich.console import Console
from rich.panel import Panel

from tifo.classifiers import CLASSIFIERS
from tifo.pipeline.confirmation import preview_folders
from tifo.pipeline.no_clustering import get_new_names

from tifo.renaming.renamer import move_flow, show_rename_results
from tifo.naming.formats import prompt_naming_format
from tifo.ui.prompts.rename import prompt_rename_option, prompt_rename_or_move

console = Console()

def embedding_prep(raw_data_list: list[dict]) -> list[dict]:
    pre_embed = [
        {
            "path": item["path"],                          # needed by place_file
            "file_name": item["file_name"],
            "stem": item.get("stem", item["file_name"]),  # kept for binary fallback
            "file_type": item.get("file_type", ""),       # needed by FileTypeClassifier
            "content": item["content"],
            "created_at": item.get("created_at"),          # needed for dated names
        }
        for item in raw_data_list
    ]
    
    return pre_embed


def get_folder_names() -> list[str]:
    folders = []

    console.print(
        Panel(
            "Enter the folder names you want files sorted into.\n"
            "Press [bold]Enter on an empty line[/bold] when you're done.",
            title="Folder Setup",
            border_style="cyan",
        )
    )

    while True:
        suffix = f"({len(folders)} added)" if folders else ""
        name = questionary.text(
            f"Folder name {suffix}",
            validate=lambda text: _validate_folder(text, folders),
        ).ask()

        # questionary returns None on Ctrl+C / Esc
        if name is None:
            break

        name = name.strip()
        if not name:  # empty line => finished
            if not folders:
                console.print("[yellow]No folders added yet.[/yellow]")
                if not questionary.confirm("Finish without any folders?", default=False).ask():
                    continue
            break

        folders.append(name)
        console.print(f"  [green]+[/green] {name}")

    if folders:
        console.print(
            Panel(
                "\n".join(f"[cyan]•[/cyan] {f}" for f in folders),
                title=f"{len(folders)} Folder(s)",
                border_style="green",
            )
        )
    return folders


def _validate_folder(text: str, existing: list[str]) -> bool | str:
    stripped = text.strip()
    if not stripped:
        return True  # empty = finish signal, handled by caller
    if stripped.lower() in (f.lower() for f in existing):
        return f"'{stripped}' already added"
    return True


def with_clustering_pipeline(*, strat_choice, raw_files, folder_labels, res) -> None:
    # 1. Prep dicts for classification
    pre_embed = embedding_prep(raw_files)
    
    # 2. Build chosen classifier    
    cls = CLASSIFIERS[strat_choice]
    if strat_choice == "manual":
        classifer = cls(model=res.embedder, folder_labels=folder_labels)
    else:
        classifer = cls()

    # 3. Do classification
    results = classifer.classify(pre_embed=pre_embed)

    # 4. Preview tree
    preview_folders(matching_results=results)
    
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
        new_names = get_new_names(results, formatter, use_date)
    else:
        new_names = [f["stem"] for f in results]

    # 7. Move (and optionally rename) each file into its matching_folder.
    renamed, skipped, failed = move_flow(results, new_names)
    show_rename_results(renamed, skipped, failed)
