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


def rename(old: str, new:str, testing_dir: str = "copy_testing") -> tuple[str, bool]:
    # Turn into Path objects
    source = Path(old)
    dest_folder = Path(testing_dir)
    
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    extension = source.suffix if not Path(new).suffix else ""
    target = dest_folder / f"{new}{extension}"
    
    if target.exists():
        return False, f"ERROR! File named '{target.name} already exists in '{dest_folder}'"
    
    
    try:
        shutil.copy2(source, target)
        return True, target.name
    except FileNotFoundError:
            return False, f"ERROR! Source file doesn't exists"
    except FileExistsError:
            return False, f"ERROR! A file named '{new}' already exists"
    except PermissionError:
            return False, "ERROR! Insuficcient permisions to rename this file"
    except OSError as e:
            return False, f"Operating System Error Occured: {e}"

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
                f"\n[green]{len(renamed)} successfully renamed[/green], "
                f"\n[yellow]{len(skipped)} skipped, "
                f"\n[red]{len(failed)}[/red]."
        )

def rename_flow(original_files, new_names):
        renamed = skipped = failed = []
        
        for f, new_name in zip(original_files, new_names):
                old_name = f["file_name"]
                
                # cases to skip
                if not new_name:
                        skipped.append((old_name, "No name generated"))
                if new_name == f["stem"]:
                        skipped.append((old_name, "Name unchanged"))
                
                success, reason = rename(f["path"], new_name)
                
                if success:
                        renamed.append((old_name, reason))
                else:
                        failed.append((old_name, reason))
        
        return renamed, skipped, failed
        

if __name__ == "__main__":
        action = ask_rename_option()
        print(action)