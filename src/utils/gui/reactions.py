from rich.console import Console

console = Console()

def select_reaction(choice: str) -> None:
    console.print(f" [green]✓[/green] {choice} selected ")