import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _is_cached(model_name: str) -> bool:
    """Best-effort check: is the model already in the HuggingFace cache?

    Used only to decide whether to warn the user about a first-run download.
    Never affects loading correctness — a wrong guess just changes a message.
    """
    cache = Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    slug = "models--sentence-transformers--" + model_name.replace("/", "--")
    return (cache / slug).exists()


def _try_load_on(device: str, status) -> "SentenceTransformer | None":
    """Load the model on `device` and verify it with a real encode.

    Returns the working model instance, or None if the device is unusable
    (e.g. CUDA build present but no usable GPU, broken driver, unsupported op).
    """
    import torch
    from sentence_transformers import SentenceTransformer

    try:
        status.update(f"[cyan]Loading weights onto {device}...[/cyan]")
        model = SentenceTransformer(MODEL_NAME, device=device)

        status.update(f"[cyan]Verifying {device} with a test encode...[/cyan]")
        _ = model.encode(["health check"], convert_to_tensor=True)
        if device == "cuda":
            torch.cuda.synchronize()
        return model
    except Exception as e:
        print(f"[device] '{device}' unavailable ({type(e).__name__}: {e})")
        return None


def load_embedder_model() -> "SentenceTransformer":
    """Load the embedder on the best working device, falling back safely.

    Order: cuda (NVIDIA CUDA or AMD ROCm on Linux) -> mps (Apple) -> cpu.
    Each candidate is verified with a real encode before being accepted, so a
    machine that merely *claims* a device but fails the forward pass degrades
    to the next option instead of crashing.

    Imports (torch / sentence_transformers) are deferred to call time so that
    code paths which never need the embedder don't pay the multi-second import.
    """
    global _model
    if _model is not None:
        return _model

    import torch
    from rich.console import Console

    console = Console()

    with console.status("[cyan]Preparing embedder...[/cyan]", spinner="dots") as status:
        status.update("[cyan]Detecting compute device...[/cyan]")
        candidates = []
        if torch.cuda.is_available():
            candidates.append("cuda")
        if torch.backends.mps.is_available():
            candidates.append("mps")
        candidates.append("cpu")

        if not _is_cached(MODEL_NAME):
            status.update("[yellow]Downloading model (first run only, ~90MB)...[/yellow]")

        for device in candidates:
            status.update(f"[cyan]Trying device: {device}...[/cyan]")
            model = _try_load_on(device, status)
            if model is not None:
                _model = model
                console.print(f"[green]✓[/green] Embedder loaded on [bold]{device}[/bold]")
                return _model

    # cpu should always succeed; if it didn't, surface the real error
    raise RuntimeError("Failed to load embedder model on any device (including CPU)")
