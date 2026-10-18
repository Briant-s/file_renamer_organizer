"""Naming router.

Holds an ordered list of strategies and dispatches each request to the first
one that can handle it. Order matters: most specific first, universal floor
last.

Extending the system:
  - New signal type (audio, video, OCR'd image text): write a strategy in
    strategies.py and insert it in DEFAULT_STRATEGIES before the floor.
  - Different model / routing policy: construct NameRouter with a custom list.

The router is intentionally tiny and holds no per-file state, so a single
instance can be reused across files and (later) shared with a worker pool.
"""

from __future__ import annotations

from tifo.naming.name_request import NameRequest, clean_stem
from tifo.naming.strategies import (
    FilenameNameStrategy,
    ImageNameStrategy,
    LLMTextNameStrategy,
    NamingStrategy,
)

# Order: images (deterministic) -> descriptive text (LLM) -> filename floor.
# The floor's can_handle always returns True, so routing never falls through.
DEFAULT_STRATEGIES: list[NamingStrategy] = [
    ImageNameStrategy(),
    LLMTextNameStrategy(),
    FilenameNameStrategy(),
]


class NameRouter:
    def __init__(self, strategies: list[NamingStrategy] | None = None) -> None:
        self.strategies = strategies if strategies is not None else DEFAULT_STRATEGIES

    def name(self, req: NameRequest) -> str:
        for strategy in self.strategies:
            if strategy.can_handle(req):
                return strategy.generate(req)
        # Defensive: should be unreachable because the floor handles everything.
        return req.formatter(clean_stem(req.original_file)) + req.suffix


# Module-level default instance for convenience (stateless, safe to share).
default_router = NameRouter()
