import questionary
from rich.console import Console
from rich.panel import Panel

from src.extractors.metadata import extract_contents
from src.ai.model import load_embedder_model
from src.clustering_flow import batch_encode

console = Console()

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


def with_clustering_pipeline(dir_path: str) -> None:
    # 1. Read & extract files first
    raw_files = extract_contents(dir_path)

    # 2. Prompt user for folder names
    folder_labels = get_folder_names()

    # 3. Load embedder and run classification
    model = load_embedder_model()
    return batch_encode(model=model, folder_labels=folder_labels, pre_embed=raw_files)
