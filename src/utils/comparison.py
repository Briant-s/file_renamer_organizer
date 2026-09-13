from rich.table import Table
from rich.console import Console

def compare_results(old_names: list[str], new_names: list[str]) -> None:
    console = Console()
    table = Table(title="Rename Preview")
    table.add_column("Original", style="red")
    table.add_column("", justify="center")
    table.add_column("New Name", style="green")
    
    for old, new in zip(old_names, new_names):
        table.add_row(old, "→", new)
    
    console.print(table)