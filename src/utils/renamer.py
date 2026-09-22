from pathlib import Path
import shutil

import questionary

from rich.console import Console
from rich.table import Table


def ask_rename_option() -> bool:
        choices = ["Accept All", "Individual Edit", "Cancel"]
        
        choice = questionary.select(
                "Apply current renames?",
                choices=choices
        ).ask()
                
        return choice


def place_file(
    src: str,
    new_stem: str,
    *,
    base_dir: str = "copy_testing",
    subfolder: str | None = None,
) -> tuple[str, str]:
    """Copy ``src`` into ``base_dir[/subfolder]`` under ``new_stem``.

    This is the single file-placement primitive shared by both pipelines:
    - no_clustering passes only ``base_dir`` (flat output)
    - with_clustering passes ``subfolder`` = the file's ``matching_folder``
      (which may itself be a nested, slash-separated relative path)

    Folder creation is lazy + idempotent (``mkdir(parents=True)``), so nested
    destinations like ``"Documents/Invoices/2026"`` work with no extra logic.
    Name collisions are resolved by appending a counter: ``name (1)``, etc.
    """
    source = Path(src)
    base = Path(base_dir)

    # Resolve the destination folder and guard against path escapes (a stray
    # ".." or leading "/" in an LLM/user-supplied folder must not write outside
    # base_dir).
    dest_folder = base / subfolder if subfolder else base
    resolved_dest = dest_folder.resolve()
    if not resolved_dest.is_relative_to(base.resolve()):
        return "false", f"ERROR! destination '{subfolder}' escapes base directory"

    resolved_dest.mkdir(parents=True, exist_ok=True)

    # Keep the source extension unless new_stem already carries one.
    extension = source.suffix if not Path(new_stem).suffix else ""
    target = resolved_dest / f"{new_stem}{extension}"

    # Dedup: never overwrite an existing file, append a counter instead.
    counter = 1
    while target.exists():
        target = resolved_dest / f"{new_stem} ({counter}){extension}"
        counter += 1

    try:
        shutil.copy2(source, target)
        return "success", target.name
    except FileNotFoundError:
        return "false", "ERROR! Source file doesn't exists"
    except PermissionError:
        return "false", "ERROR! Insuficcient permisions to rename this file"
    except OSError as e:
        return "false", f"Operating System Error Occured: {e}"

def show_rename_results(renamed, skipped, failed) -> None:
        console = Console()
        table = Table(title="Rename Results")
        
        table.add_column("Status", style="bold")
        table.add_column("File")
        table.add_column("Detail")
        
        for old_name, new_name in renamed:
                table.add_row("[green]RENAMED[/green]", old_name, f"→ {new_name}")
        for old_name, reason in skipped:
                table.add_row("[yellow]SKIPPED[/yellow]", old_name, reason)
        for old_name, reason in failed:
                table.add_row("[red]FAILED[/red]", old_name, reason)
        
        console.print(table)
        console.print(
                f"\n[green]{len(renamed)} files renamed[/green], "
                f"\n[yellow]{len(skipped)} files skipped, "
                f"\n[red]{len(failed)} files failed[/red]."
        )

def rename_flow(original_files, new_names, *, base_dir: str = "copy_testing"):
    """Flat rename (no folders). Skips files with no/unchanged name."""
    renamed = []
    skipped = []
    failed = []

    for f, new_name in zip(original_files, new_names):
        old_name = f["file_name"]

        # cases to skip — nothing to move to in the flat case, so skip entirely
        if not new_name:
            skipped.append((old_name, "No name generated"))
            continue
        if new_name == f["stem"]:
            skipped.append((old_name, "Name unchanged"))
            continue

        success, reason = place_file(f["path"], new_name, base_dir=base_dir)

        if success == "success":
            renamed.append((old_name, reason))
        elif success == "skipped":
            skipped.append((old_name, reason))
        else:
            failed.append((old_name, reason))

    return renamed, skipped, failed


def move_flow(original_files, new_names, *, base_dir: str = "copy_testing"):
    """Move each file into its ``matching_folder`` (nested paths allowed).

    Unlike ``rename_flow``, the move ALWAYS happens even when the name is
    unchanged — "just move" is a valid outcome. ``new_names`` carries the stem
    to use (original stem for move-only, generated name for rename+move).
    Files with no ``matching_folder`` go to an ``Unsorted`` subfolder so they
    are surfaced rather than silently dropped.
    """
    renamed = []
    skipped = []
    failed = []

    for f, new_name in zip(original_files, new_names):
        old_name = f["file_name"]
        subfolder = f.get("matching_folder") or "Unsorted"

        # Fall back to the original stem if no name was generated — move-only.
        stem = new_name or f["stem"]

        success, reason = place_file(
            f["path"], stem, base_dir=base_dir, subfolder=subfolder
        )

        if success == "success":
            renamed.append((old_name, f"{subfolder}/{reason}"))
        elif success == "skipped":
            skipped.append((old_name, reason))
        else:
            failed.append((old_name, reason))

    return renamed, skipped, failed
        

if __name__ == "__main__":
        action = ask_rename_option()
        print(action)