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


def _try_load_on(device: str, status, *, quiet: bool = False) -> "SentenceTransformer | None":
    """Load the model on `device` and verify it with a real encode.

    Returns the working model instance, or None if the device is unusable
    (e.g. CUDA build present but no usable GPU, broken driver, unsupported op).
    """
    import torch
    from sentence_transformers import SentenceTransformer

    try:
        status.update(f"[cyan]Loading weights onto {device}...[/cyan]")
        model = SentenceTransformer(MODEL_NAME, device=device, local_files_only=True)

        status.update(f"[cyan]Verifying {device} with a test encode...[/cyan]")
        _ = model.encode(["health check"], convert_to_tensor=True)
        if device == "cuda":
            torch.cuda.synchronize()
        return model
    except Exception as e:
        if not quiet:
            print(f"[device] '{device}' unavailable ({type(e).__name__}: {e})")
        return None


class _NullStatus:
    """No-op stand-in for rich's console.status (used in quiet mode)."""

    def update(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        pass


def load_embedder_model(*, quiet: bool = False) -> "SentenceTransformer":
    """Load the embedder on the best working device, falling back safely.

    Order: cuda (NVIDIA CUDA or AMD ROCm on Linux) -> mps (Apple) -> cpu.
    Each candidate is verified with a real encode before being accepted, so a
    machine that merely *claims* a device but fails the forward pass degrades
    to the next option instead of crashing.

    ``quiet=True`` suppresses ALL console output (rich spinner + prints). The
    Streamlit GUI uses this so model-loading status never leaks to the terminal
    that launched the server; the CLI leaves it False for its live spinner.

    Imports (torch / sentence_transformers) are deferred to call time so that
    code paths which never need the embedder don't pay the multi-second import.
    """
    global _model
    if _model is not None:
        return _model

    import torch
    from rich.console import Console

    console = Console(quiet=quiet)

    # In quiet mode (GUI), also silence the tqdm "Loading weights" bar that
    # transformers/safetensors print directly via tqdm — rich suppression alone
    # doesn't cover it. HuggingFace honors this env var; set it before loading.
    if quiet:
        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
        try:
            from transformers.utils import logging as _hf_logging

            _hf_logging.disable_progress_bar()
        except Exception:
            pass

    # In quiet mode use a no-op status so nothing renders; otherwise the real
    # rich spinner. Both support .update()/context-manager, so the body is shared.
    status_cm = _NullStatus() if quiet else console.status(
        "[cyan]Preparing embedder...[/cyan]", spinner="dots"
    )

    with status_cm as status:
        status.update("[cyan]Detecting compute device...[/cyan]")
        candidates = []
        if torch.cuda.is_available():
            candidates.append("cuda")
        if torch.backends.mps.is_available():
            candidates.append("mps")
        candidates.append("cpu")

        if not _is_cached(MODEL_NAME):
            # We run fully offline (HF_HUB_OFFLINE=1), so a missing cache cannot
            # be recovered by downloading. Fail early with an actionable message
            # instead of letting SentenceTransformer raise an opaque network error.
            raise RuntimeError(
                f"Embedding model '{MODEL_NAME}' is not in the local HuggingFace cache "
                f"and TiFo runs offline. Pull it once while online with:\n\n"
                f"    HF_HUB_OFFLINE=0 python -c "
                f"\"from sentence_transformers import SentenceTransformer; "
                f"SentenceTransformer('{MODEL_NAME}')\"\n\n"
                f"After it is cached, TiFo will load it without any network access."
            )

        for device in candidates:
            status.update(f"[cyan]Trying device: {device}...[/cyan]")
            model = _try_load_on(device, status, quiet=quiet)
            if model is not None:
                _model = model
                if not quiet:
                    console.print(
                        f"[green]✓[/green] Embedder loaded on [bold]{device}[/bold]"
                    )
                return _model

    # cpu should always succeed; if it didn't, surface the real error
    raise RuntimeError("Failed to load embedder model on any device (including CPU)")
