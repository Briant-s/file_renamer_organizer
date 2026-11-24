from __future__ import annotations

# Embedder: multilingual MiniLM (English + Indonesian file contents).
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# LLM: qwen2.5:3b for naming + cluster labeling.
LLM_MODEL = "qwen2.5:3b"
RENAME_MODEL = "qwen2.5:1.5b"


PROPERTIES = {"temperature": 0, "seed": 0, "num_predict": 40,
              "num_ctx": 4096, "num_thread": 4, "num_gpu": 0}
