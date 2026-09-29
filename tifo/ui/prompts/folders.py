import questionary
from rich.console import Console
from rich.panel import Panel


console = Console()


def validate_folder(text: str, existing: list[str]) -> bool | str:
    stripped = text.strip()
    if not stripped:
        return True  # empty = finish signal, handled by caller
    if stripped.lower() in (f.lower() for f in existing):
        return f"'{stripped}' already added"
    return True

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
            validate=lambda text: validate_folder(text, folders),
        ).ask()

        # questionary returns None on Ctrl+C / Esc
        if name is None:
            raise KeyboardInterrupt

        name = name.strip()
        if not name:  # empty line => finished
            if not folders:
                console.print("[yellow]No folders added yet.[/yellow]")
                confirm_no_folders = questionary.confirm("Finish without any folders?", default=False).ask() 
                if confirm_no_folders is None:
                    raise KeyboardInterrupt
                elif not confirm_no_folders:
                    continue
            break

        folders.append(name)
        console.print(f"  [green]+[/green] {name}")

    # Warn on a single folder: the classifier has nothing to compare against,
    # so every file either lands in that one folder or falls to Unsorted.
    if len(folders) == 1:
        console.print(
            Panel(
                "You added only [bold]one folder[/bold]. With a single folder there's "
                "nothing to compare against — files will either go into it or land in "
                "[yellow]Unsorted[/yellow].",
                title="⚠ Single folder",
                border_style="yellow",
            )
        )

    if folders:
        console.print(
            Panel(
                "\n".join(f"[cyan]•[/cyan] {f}" for f in folders),
                title=f"{len(folders)} Folder(s)",
                border_style="green",
            )
        )
    return folders