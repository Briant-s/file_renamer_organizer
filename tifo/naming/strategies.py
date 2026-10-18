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

from typing import Protocol, runtime_checkable

from ollama import chat
from pydantic import BaseModel

from tifo.naming.name_request import NameRequest, clean_stem, finalize


# --- shared schema for LLM responses ---------------------------------------

class FileMetaData(BaseModel):
    topic: str
    date: str | None = None  # YYYY-MM-DD if found in content, else None


LLM_MODEL = "llama3.2:3b"
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
            options={"temperature": 0},
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
