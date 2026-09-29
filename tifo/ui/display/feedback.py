from contextlib import contextmanager
from rich.console import Console

_CANCEL_VALUES = {"cancel", "exit", "abort", "quit"}

console = Console()

@contextmanager
def loading(message: str):
    with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
        yield


def select_reaction(choice: str | None) -> None:
    if choice is None:
        console.print(f"[yellow]•[/yellow] [dim]cancelled[/dim]")
        return
    elif str(choice).strip().lower() in _CANCEL_VALUES:
        console.print(f"[yellow]•[/yellow] [dim]{choice}[/dim]")
        return
    else:
        console.print(f" [green]✓[/green] {choice} selected ")
    