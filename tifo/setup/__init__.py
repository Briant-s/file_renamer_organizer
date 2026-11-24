"""First-run setup for TiFo.

TiFo runs fully offline (``HF_HUB_OFFLINE=1`` is set in ``tifo.app``), so the
embedding model must already be in the local HuggingFace cache before the app
starts. A fresh install has an empty cache, so the very first run would fail
with a "model not cached" error. This package pulls the model once, online,
and records that setup is done so later runs skip the check cheaply.
"""

from tifo.setup.embedder import (
    embedder_cached,
    ensure_embedder,
    run_setup,
    setup_complete,
)

__all__ = [
    "embedder_cached",
    "ensure_embedder",
    "run_setup",
    "setup_complete",
]
