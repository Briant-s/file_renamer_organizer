from pathlib import Path

def display_path(dir_path: str) -> str:
    p = Path(dir_path).expanduser().resolve()
    try:
        return f"~/{p.relative_to(Path.home())}"
    except ValueError:
        return str(p)