"""Naming strategies.

Each strategy implements two methods:
  - can_handle(req) -> bool : whether this strategy applies to the request
  - generate(req)   -> str  : produce the final file name

Strategies are top-level, side-effect-free objects (no printing, no shared
mutable state) so they stay picklable and safe to run in worker processes when
parallel naming is added later. To add a new signal (audio tags, OCR, video
metadata), write a new strategy class and register it in router.py — nothing
else needs to change.
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from ollama import chat
from pydantic import BaseModel

from tifo.config import LLM_MODEL, RENAME_MODEL, PROPERTIES # re-exported for strategies in this module
from tifo.naming.name_request import NameRequest, clean_stem, finalize


# --- shared schema for LLM responses ---------------------------------------

class FileMetaData(BaseModel):
    topic: str
    date: str | None = None  # YYYY-MM-DD if found in content, else None


class BatchItem(BaseModel):
    """One file's result inside a batch response. ``id`` echoes the input id so
    results are joined by id, never by list position."""

    id: int
    topic: str
    date: str | None = None  # YYYY-MM-DD if found in content, else None


class BatchResult(BaseModel):
    results: list[BatchItem]


MAX_CONTENT_CHARS = 1000

# Image suffixes handled by the EXIF-aware deterministic strategy.
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".tiff", ".tif", ".webp", ".png", ".heic", ".heif"}


@runtime_checkable
class NamingStrategy(Protocol):
    def can_handle(self, req: NameRequest) -> bool: ...
    def generate(self, req: NameRequest) -> str: ...


# --- image: deterministic, no LLM ------------------------------------------

class ImageNameStrategy:
    """Name images deterministically from EXIF + filename.

    Images carry no readable subject — only factual metadata (date / device /
    location / dimensions). A small LLM asked to compose a name from those
    hallucinates dates and drops the unique filename identifier, collapsing
    distinct photos together. So we assemble the name in code: zero
    hallucination, and every file stays unique because the filename stem is
    always included.

    Name shape: "<Camera> <FilenameStem>", date-prefixed from a REAL EXIF
    capture date when the user chose a dated format.
    """

    def can_handle(self, req: NameRequest) -> bool:
        return req.ext in IMAGE_SUFFIXES

    @staticmethod
    def _compact_device(device: str) -> str:
        # "NIKON CORPORATION NIKON Z 8" -> "NIKON Z 8"
        words = [w for w in device.split() if w.lower() != "corporation"]
        compact: list[str] = []
        for w in words:
            if not compact or compact[-1].lower() != w.lower():
                compact.append(w)
        return " ".join(compact)

    def generate(self, req: NameRequest) -> str:
        md = req.metadata or {}
        stem = clean_stem(req.original_file)

        parts: list[str] = []
        device = md.get("device")
        if device:
            parts.append(self._compact_device(device))
        parts.append(stem)  # always present -> guarantees uniqueness

        topic = " ".join(p for p in parts if p).strip() or stem
        # Only a real EXIF capture date may prefix the name (never invented).
        return finalize(topic, req, explicit_date=md.get("date_taken"))


# --- descriptive text: LLM --------------------------------------------------

class LLMTextNameStrategy:
    """Name files that have real descriptive text by asking the LLM for a topic.

    This is the only strategy that calls the model, and only when there is
    genuine content to summarize — so the model is never asked to invent a name
    from nothing (which is what produced hallucinations like 'meeting minutes').
    """

    def can_handle(self, req: NameRequest) -> bool:
        return bool(req.content and req.content.strip())

    def generate(self, req: NameRequest) -> str:
        truncated = " ".join(req.content.split())[:MAX_CONTENT_CHARS]

        date_instruction = (
            "- If the content mentions a specific date (invoice/report/meeting date), "
            "extract it as YYYY-MM-DD in the date field. Otherwise return null.\n"
            if req.use_date else
            "- Set date to null.\n"
        )
        prompt = (
            "Read the file content below and return a short descriptive title "
            "(2-4 words) that describes what the file is about.\n\n"
            "Rules:\n"
            "- Return only the title words, no extension, no punctuation, no explanation\n"
            "- Be specific, not generic (e.g. 'Grocery Shopping List' not 'Text Document')\n"
            f"{date_instruction}"
            f"\nContent:\n{truncated}"
        )

        result = chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format=FileMetaData.model_json_schema(),
            options=PROPERTIES
        )
        ai = FileMetaData.model_validate_json(result.message.content)
        return finalize(ai.topic, req, explicit_date=ai.date)


# --- floor: cleaned filename, no LLM ---------------------------------------

class FilenameNameStrategy:
    """Universal floor: derive the name from the cleaned original filename.

    Always applicable, so it is registered last and guarantees the router always
    produces a name. Used for content-less files (binaries, EXIF-less images that
    somehow reach here, encrypted archives) without ever calling the LLM.
    """

    def can_handle(self, req: NameRequest) -> bool:
        return True

    def generate(self, req: NameRequest) -> str:
        return finalize(clean_stem(req.original_file), req)


# --- batched descriptive naming (LLM) --------------------------------------

# Batching sends several files' content in one chat() call to cut per-call
# overhead (prompt-eval + round-trip) for folders with many text files.
# Accuracy is preserved by: stable integer ids echoed back (join by id, not
# order), a per-item JSON schema, a small chunk size, and single-file fallback
# for any id the model fails to return.
BATCH_SIZE = 4
BATCH_CONTENT_CHARS = 500  # tighter than MAX_CONTENT_CHARS to fit many per prompt


def name_batch(
    reqs: list[NameRequest],
    *,
    chunk_size: int = BATCH_SIZE,
    on_chunk: Callable[[int], None] | None = None,
) -> dict[int, str]:
    """Name many descriptive-text files in grouped LLM calls.

    Returns ``{index_in_reqs: final_name}``. Any file the batch fails to return
    is simply absent from the result — the caller falls back to single-file
    naming for those ids. ``reqs`` must be LLM-eligible (real content); route
    images/empty files through their deterministic strategies instead.
    """
    out: dict[int, str] = {}
    done = 0

    for start in range(0, len(reqs), chunk_size):
        chunk = reqs[start : start + chunk_size]

        lines: list[str] = []
        for offset, r in enumerate(chunk):
            gid = start + offset
            snippet = " ".join((r.content or "").split())[:BATCH_CONTENT_CHARS]
            lines.append(f"[id {gid}] filename: {r.original_file}\n{snippet}")

        prompt = (
            "For EACH numbered file below, return a short descriptive title "
            "(2-4 words) describing what that file is about.\n\n"
            "Rules:\n"
            "- Echo back the SAME id for each file.\n"
            "- Base each title ONLY on that file's own content — do not mix files.\n"
            "- Return only title words: no extension, no punctuation, no explanation.\n"
            "- Be specific, not generic (e.g. 'Grocery Shopping List' not 'Text Document').\n"
            "- If a file mentions a specific date (invoice/report/meeting), extract it as "
            "YYYY-MM-DD in that item's date field; otherwise null.\n\n"
            "Files:\n" + "\n\n".join(lines)
        )

        # num_predict must scale with the number of files or the JSON truncates
        # mid-array and the tail items are lost. num_ctx must fit the chunk.
        batch_options = {
            **PROPERTIES,
            "num_predict":  24 * len(chunk),
            "num_ctx": max(PROPERTIES.get("num_ctx", 2048), 1024 + 400 * len(chunk)),
        }

        try:
            resp = chat(
                model=RENAME_MODEL,
                messages=[{"role": "user", "content": prompt}],
                format=BatchResult.model_json_schema(),
                options=batch_options,
                keep_alive="10m"
            )
            parsed = BatchResult.model_validate_json(resp.message.content)
        except Exception:
            # Whole-chunk failure: leave these ids unset so the caller falls back.
            done += len(chunk)
            if on_chunk is not None:
                on_chunk(done)
            continue

        by_id = {item.id: item for item in parsed.results}
        for offset, r in enumerate(chunk):
            gid = start + offset
            item = by_id.get(gid)
            if item is None or not item.topic.strip():
                continue  # missing/empty -> caller handles via single-file fallback
            out[gid] = finalize(item.topic, r, explicit_date=item.date)

        done += len(chunk)
        if on_chunk is not None:
            on_chunk(done)

    return out
