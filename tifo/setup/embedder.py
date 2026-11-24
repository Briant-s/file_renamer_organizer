"""Download the embedding model on first run and remember it was done.

The app runs offline, so the embedder has to be present in the HuggingFace
cache before anything tries to load it. On a first run that cache is empty.
``ensure_embedder`` fixes that: it checks the cache, and if the model is
missing it temporarily turns HF's offline flags off, downloads the model with
a visible spinner, and writes a marker file so future runs don't re-check.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from tifo.config import EMBED_MODEL

# Kept in sync with tifo.common.recent so all TiFo state lives together.
_MARKER_VERSION = 1


def _config_dir() -> Path:
    """TiFo config directory, honoring XDG_CONFIG_HOME (matches recent.py)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "tifo"


def _marker_path() -> Path:
    return _config_dir() / "setup.json"


def _hf_cache_dir() -> Path:
    return Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"


def embedder_cached(model_name: str = EMBED_MODEL) -> bool:
    """True when the embedder weights are already in the local HF cache.

    Mirrors ``tifo.embedding.model._is_cached``; duplicated intentionally so
    setup never imports torch / sentence-transformers just to answer this.
    """
    slug = "models--sentence-transformers--" + model_name.replace("/", "--")
    return (_hf_cache_dir() / slug).exists()


def setup_complete() -> bool:
    """True when a previous run recorded that setup finished for this model.

    The marker is a fast path only. If the HF cache was cleared after the
    marker was written, ``ensure_embedder`` still re-checks the cache and
    re-downloads, so a stale marker can never cause a broken offline run.
    """
    try:
        data = json.loads(_marker_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError):
        return False
    return (
        isinstance(data, dict)
        and data.get("embedder_model") == EMBED_MODEL
        and bool(data.get("completed_at"))
    )


def _write_marker(model_name: str) -> None:
    path = _marker_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _MARKER_VERSION,
            "embedder_model": model_name,
            "completed_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        # The marker is only an optimization; never fail setup over it.
        pass


def _download_embedder(model_name: str, *, quiet: bool) -> None:
    """Pull the model into the HF cache with HF offline mode turned OFF.

    ``tifo.app`` sets HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE for the whole
    process. Downloading needs network, so we clear those two vars for the
    duration of the download and restore whatever they were afterwards —
    leaving the rest of the process in its original offline state.
    """
    saved = {
        key: os.environ.get(key)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    }
    os.environ["HF_HUB_OFFLINE"] = "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    try:
        from sentence_transformers import SentenceTransformer

        # Constructing with the default (online) settings downloads any
        # missing files into the cache. We don't keep the instance; the app
        # loads it later from cache with local_files_only=True.
        SentenceTransformer(model_name)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def ensure_embedder(*, quiet: bool = False, force: bool = False) -> bool:
    """Make sure the embedder is cached, downloading it once if needed.

    Returns True when the model is present (already cached or freshly
    downloaded), False when a required download failed (e.g. offline with an
    empty cache). Safe to call on every launch: when the model is already
    cached it just writes/refreshes the marker and returns quickly.
    """
    from rich.console import Console

    console = Console(quiet=quiet)

    if embedder_cached() and not force:
        if not setup_complete():
            _write_marker(EMBED_MODEL)
        return True

    console.print(
        f"[cyan]First-time setup:[/cyan] downloading embedding model "
        f"[bold]{EMBED_MODEL}[/bold].\n"
        f"[dim]This runs once and needs an internet connection. "
        f"Later runs are fully offline.[/dim]"
    )

    status_cm = console.status(
        "[cyan]Downloading embedder (this may take a few minutes)...[/cyan]",
        spinner="dots",
    )
    try:
        with status_cm:
            _download_embedder(EMBED_MODEL, quiet=quiet)
    except Exception as e:  # network error, disk full, etc.
        console.print(
            f"[red]✗[/red] Could not download the embedding model "
            f"([bold]{type(e).__name__}[/bold]: {e}).\n"
            f"[dim]Check your internet connection and run [bold]tifo-setup[/bold] "
            f"again, or pull it manually:[/dim]\n\n"
            f"    HF_HUB_OFFLINE=0 python -c "
            f"\"from sentence_transformers import SentenceTransformer; "
            f"SentenceTransformer('{EMBED_MODEL}')\"\n"
        )
        return False

    if not embedder_cached():
        console.print(
            "[red]✗[/red] Download finished but the model is still not in the "
            "cache. Please run [bold]tifo-setup[/bold] again."
        )
        return False

    _write_marker(EMBED_MODEL)
    console.print(f"[green]✓[/green] Embedding model ready. TiFo is set up.")
    return True


def run_setup() -> None:
    """Console-script entry point for ``tifo-setup``.

    Runs the download unconditionally re-checking the cache, prints a short
    summary, and exits non-zero if the model could not be made available so
    scripts/CI can detect failure.
    """
    from rich.console import Console

    console = Console()
    console.print("[bold]TiFo setup[/bold]\n")

    ok = ensure_embedder(quiet=False)

    if ok:
        console.print("\n[green]Setup complete.[/green] Run [bold]tifo[/bold] to start.")
        raise SystemExit(0)

    console.print("\n[red]Setup did not complete.[/red] See the message above.")
    raise SystemExit(1)


if __name__ == "__main__":
    run_setup()
