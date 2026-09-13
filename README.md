# AI File Renamer & Organizer

A local, privacy-first CLI tool that uses a local LLM to automatically rename and organize files based on their actual content — no cloud, no API keys, runs on Windows, Linux, and macOS.

---

## Goal

Given a folder of mixed files (documents, notes, spreadsheets, images, videos, PDFs, etc.), the tool should:
1. Read and understand each file's content
2. Suggest a clean, descriptive filename
3. Classify the file into a user-defined folder
4. Apply the changes — or preview them first and let the user confirm

---

## Current State

- [x] Text file extraction (`src/extractors/metadata.py`)
- [x] Folder classification via semantic embeddings (`src/clustering_flow.py`)
- [x] Label expansion via local LLM — Ollama + llama3.2:1b (`src/ai/expand_label.py`)
- [x] File renaming utility (`src/utils/renamer.py`)
- [x] AI name generation for text files (`src/ai/generator.py`)
- [x] Basic CLI menu (`main.py`)
- [x] Safe handling of binary files (skips unreadable files gracefully)

---

## Roadmap

### Phase 1 — Content Extraction (multi-file type support)
The current extractor only handles plain text. Expand it to support all common file types.

| File Type | Extraction Method | Library |
|---|---|---|
| `.txt`, `.md`, `.csv`, `.log` | Direct `read_text()` | stdlib |
| `.pdf` | Extract text layer; fallback to OCR if scanned | `pymupdf` (fitz) |
| `.docx` | Parse XML body text | `python-docx` |
| `.xlsx`, `.csv` | Read cell values | `openpyxl`, stdlib |
| `.pptx` | Extract slide text | `python-pptx` |
| `.jpg`, `.png`, etc. | EXIF metadata + optional image captioning | `Pillow`, `exifread` |
| `.mp4`, `.mkv`, etc. | Extract filename/metadata; optional audio transcription | `ffmpeg-python`, `whisper` |
| `.mp3`, `.wav`, etc. | Optional audio transcription | `openai-whisper` (local) |

Each extractor should return a normalized dict with at minimum:
```python
{
    "content": str | None,   # extracted text
    "summary": str | None,   # optional pre-summarized text for large files
    "metadata": dict          # type-specific metadata (EXIF, duration, page count, etc.)
}
```

Add each extractor as a separate file under `src/extractors/` (e.g. `pdf.py`, `docx.py`, `image.py`).

---

### Phase 2 — Smarter Name Generation
The current name generator does a single LLM call and returns a 2-word topic. Improve it:

- For text-heavy files (docs, PDFs): summarize first, then derive a name from the summary
- For binary files with no content: use filename stem + metadata (e.g. image dimensions, creation date)
- Name format options: `snake_case`, `Title Case`, `kebab-case` — user configurable
- Deduplication: if a generated name already exists in the folder, append a counter or date

---

### Phase 3 — Improved Classification
The current embedding-based classifier works but has a few weak spots to address:

- **Threshold tuning**: the current z-score and raw cosine thresholds are hardcoded. Make them configurable or auto-tuned based on score distribution.
- **Unclassified bucket**: files that score below threshold (currently `matching_folder = None`) should be surfaced to the user explicitly as "Unsorted" rather than silently dropped.
- **Multi-label hint**: if the top-2 scores are very close, flag the file as ambiguous and let the user pick.
- **Hybrid signal**: for binary files, combine filename stem embedding with any extracted metadata text.

---

### Phase 4 — Preview & Confirmation UI
Before applying any changes, show the user a diff-style preview:

```
[Rename]   3.txt              →  Passwords & Credentials.txt
[Move]     3.txt              →  Financial Files/
[Rename]   1.txt              →  Weekly To-Do List.txt
[Move]     1.txt              →  Household Chores/
[UNSORTED] app_idea_notes.txt →  No confident match
```

Let the user:
- Accept all
- Reject all
- Edit individual entries interactively

The `simple-term-menu` library already in the project can power this.

---

### Phase 5 — Cross-Platform & Packaging
Make the tool installable and runnable on Windows, Linux, and macOS.

- Replace `simple-term-menu` with a cross-platform alternative like `questionary` or `InquirerPy` — `simple-term-menu` does not work on Windows.
- Add a `run.bat` and `run.sh` launcher for users who don't want to use `uv`/`pip` directly.
- Package with `pyinstaller` or `uv` for single-file distribution if needed.
- Test on Windows (PowerShell + CMD), macOS (zsh), Linux (bash).

> **Note:** Ollama itself is cross-platform and the setup is identical on all three OSes, so the LLM layer needs no changes.

---

### Phase 6 — Configuration File
Add a `config.toml` or `.env` so users can set preferences without touching code:

```toml
[general]
preview_before_apply = true
naming_format = "Title Case"        # or "snake_case", "kebab-case"
default_output_dir = ""             # empty = rename in-place

[model]
ollama_model = "llama3.2:1b"        # swap to llama3.1:8b for better quality
embedder_model = "all-MiniLM-L6-v2"

[classification]
min_confidence = 0.15               # raw cosine threshold (small batch)
min_z_score = 1.0                   # z-score threshold (large batch, 20+ files)
min_gap = 0.05                      # min gap between top-2 scores

[extractors]
enable_ocr = false                  # requires tesseract installed
enable_whisper = false              # audio/video transcription, slow on CPU
```

---

## Tech Stack

| Layer | Current | Planned additions |
|---|---|---|
| LLM backend | Ollama + llama3.2:1b | Configurable model (llama3.1:8b recommended for quality) |
| Embeddings | `sentence-transformers` all-MiniLM-L6-v2 | Same — fast and accurate enough |
| PDF extraction | — | `pymupdf` |
| Word/Excel/PPT | — | `python-docx`, `openpyxl`, `python-pptx` |
| Image metadata | — | `Pillow`, `exifread` |
| Audio/video | — | `openai-whisper` (local), `ffmpeg-python` |
| CLI UI | `simple-term-menu` | `questionary` or `InquirerPy` (Windows-compatible) |
| Config | hardcoded | `tomllib` (stdlib in Python 3.11+) |
| Packaging | `uv` | `pyinstaller` for distributable builds |

---

## Project Structure (target)

```
file_renamer/
├── main.py
├── config.toml                   # user configuration
├── pyproject.toml
├── src/
│   ├── clustering_flow.py        # folder classification pipeline
│   ├── ai/
│   │   ├── model.py              # embedder loader
│   │   ├── generator.py          # name generation
│   │   ├── expand_label.py       # folder label expansion
│   │   └── text_sampler.py       # sample builder for LLM context
│   ├── extractors/
│   │   ├── metadata.py           # file system metadata + plain text
│   │   ├── pdf.py                # PDF text extraction
│   │   ├── docx.py               # Word document extraction
│   │   ├── spreadsheet.py        # Excel/CSV extraction
│   │   ├── image.py              # EXIF + optional captioning
│   │   └── audio_video.py        # Whisper transcription
│   └── utils/
│       ├── renamer.py            # file rename/move logic
│       └── preview.py            # diff preview UI
```

---

## Getting Started (current)

**Prerequisites:** Python 3.13+, [Ollama](https://ollama.com) installed and running, `llama3.2:1b` pulled.

```bash
# Install dependencies
uv sync

# Pull the LLM model
ollama pull llama3.2:1b

# Run
uv run main.py
```
