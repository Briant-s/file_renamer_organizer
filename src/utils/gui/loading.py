from contextlib import contextmanager
from rich.console import Console

console = Console()

@contextmanager
def loading(message: str):
    with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
        yield