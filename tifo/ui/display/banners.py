from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

from tifo.common.paths import display_path

console = Console()


def _detail(value: str, value_style: str, suffix: str) -> None:
    grid = Table.grid(padding=(0, 1))
    grid.add_column(width=2, no_wrap=True)   
    grid.add_column(overflow="fold")         
    grid.add_row(
        Text(" >", style="bold"),
        Text.assemble((value, value_style), (f" {suffix}", "dim")),
    )
    console.print(grid)

def welcome_banner() -> None:
    title = Text()
    title.append("Ti", style="bold white")
    title.append("Fo", style="bold green4")

    body = Text.assemble(
        title,
        ("  —  rename & organize files by their content\n", "dim"),
        ("Local, private, offline.", "dim italic"),
    )

    console.print(
        Panel(
            body,
            border_style="green4",
            padding=(1, 2),
            box= box.DOUBLE,
            expand=False,
        )
    )
    console.file.flush()


def renaming_banner(working_dir: str) -> None:
    
    title = Text.assemble(
        ("Renaming", "bold dark_cyan"),
        (" Flow", "bold white"),
    )

    console.print()
    console.print(Rule(title, style="dark_cyan", align="center"))
    _detail(display_path(working_dir), "dark_cyan", "set as working directory")


def clustering_banner(selected_mode: str, working_dir: str) -> None:
    title = Text.assemble(
        ("Clustering", "bold orange3"),
        (" Flow", "bold white"),
        
    )

    console.print()
    console.print(Rule(title, style="orange3", align="center"))
    _detail(selected_mode, "orange3", "mode selected")
    _detail(display_path(working_dir), "orange3", "set as working directory")
