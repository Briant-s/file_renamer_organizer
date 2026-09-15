import torch
from sentence_transformers import SentenceTransformer

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _try_load_on(device: str) -> SentenceTransformer | None:
    """Load the model on `device` and verify it with a real encode.

    Returns the working model instance, or None if the device is unusable
    (e.g. CUDA build present but no usable GPU, broken driver, unsupported op).
    """
    try:
        model = SentenceTransformer(MODEL_NAME, device=device)
        _ = model.encode(["health check"], convert_to_tensor=True)
        if device == "cuda":
            torch.cuda.synchronize()
        return model
    except Exception as e:
        print(f"[device] '{device}' unavailable ({type(e).__name__}: {e})")
        return None


def load_embedder_model() -> SentenceTransformer:
    """Load the embedder on the best working device, falling back safely.

    Order: cuda (NVIDIA CUDA or AMD ROCm on Linux) -> mps (Apple) -> cpu.
    Each candidate is verified with a real encode before being accepted, so a
    machine that merely *claims* a device but fails the forward pass degrades
    to the next option instead of crashing.
    """
    global _model
    if _model is not None:
        return _model

    print("Loading embedder model")

    candidates = []
    if torch.cuda.is_available():
        candidates.append("cuda")
    if torch.backends.mps.is_available():
        candidates.append("mps")
    candidates.append("cpu")

    for device in candidates:
        model = _try_load_on(device)
        if model is not None:
            print(f"Embedder model loaded on {device}")
            _model = model
            return _model

    # cpu should always succeed; if it didn't, surface the real error
    raise RuntimeError("Failed to load embedder model on any device (including CPU)")
