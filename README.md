<div align="center">

# TiFo

<img src="demo/tifo.gif" width="800" alt="TiFo demo">

**Rename and organize your files by their actual content — locally, privately, offline.**

</div>

TiFo is a command-line tool that reads what your files are _about_, gives them clean,
descriptive names, and sorts them into folders that make sense. It runs entirely on your
machine using a local LLM (via [Ollama](https://ollama.com)) and local embeddings — no
cloud, no API keys, nothing leaves your computer.

Point it at a folder of messy files like `1.txt`, `report(final)(2).docx`, or `IMG_4821.pdf`,
and get back `Weekly To-Do List.txt`, `Q3 Financial Summary.docx`, and a tidy folder tree.

> [!WARNING]
> TiFo **renames and moves your files in place**. This is a destructive operation and
> **cannot be undone**. You are shown a full preview and must confirm before anything
> changes — but there is no automatic backup. Back up important folders, or try TiFo on a
> copy first.

## Features

- **Content-aware renaming** — extracts text from each file and asks a local LLM for a short,
  specific title (e.g. `Grocery Shopping List`, not `Text Document`).
- **Multi-format extraction** — plain text, Markdown, CSV, logs, PDF, Word (`.docx`), and
  Excel (`.xlsx`). Binary and unreadable files are handled gracefully.
- **Two workflows** — rename files in place, or rename _and_ organize them into folders.
- **Two folder strategies**:
  - _Manual + semantic_ — you name the folders, TiFo places files by embedding similarity,
    with guided prompts to help you pick effective folder names.
  - _By file type_ — sorts into `Documents`, `Images`, `Spreadsheets`, `Code`, and more.
- **Flexible naming formats** — `Title Case`, `snake_case`, `kebab-case`, `lowercase`,
  `UPPERCASE`, plus date-prefixed variants (`YYYY-MM-DD ...`).
- **Preview before applying** — see a rename table or a folder tree, then accept or cancel.
  After applying, TiFo tells you exactly where your files ended up.
- **Safe by design** — collision-safe deduplication, an explicit `Unsorted` bucket for
  low-confidence matches, path-escape guards, and graceful `Ctrl+C` exit at any prompt.
- **Cross-hardware** — CPU by default, with automatic fallback across CUDA → Apple MPS → CPU.

## How it works

```
   folder of files
        │
        ▼
  ┌───────────────┐    extract text from txt / md / csv / pdf / docx / xlsx
  │  Extractors   │
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐    local LLM (Ollama) suggests a short descriptive title
  │  Name gen     │    per file, formatted to your chosen style
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐    (organize mode) embed file content + folder labels,
  │  Classifier   │    match via cosine similarity, gate by confidence
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐    table/tree preview → your confirmation → move into place
  │  Preview +    │
  │  Apply        │
  └───────────────┘
```

- **Embeddings** use `sentence-transformers` with the `all-MiniLM-L6-v2` model.
- **Naming and label expansion** use the `llama3.2:3b` model through Ollama.
- For folder classification, labels are expanded into richer descriptions before embedding.
  A file is assigned only when its top match clears a confidence threshold _and_ beats the
  runner-up by a margin; otherwise it is routed to `Unsorted`.

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **[Ollama](https://ollama.com)** installed and running
- The `llama3.2:3b` model pulled locally

## Getting started

```bash
# 1. Clone the stable branch
git clone -b stable https://github.com/Briant-s/file_renamer_organizer.git
cd file_renamer_organizer

# 2. Install dependencies (CPU wheels by default)
uv sync

# 3. Pull the LLM model
ollama pull llama3.2:3b

# 4. Run
uv run tifo
```

On first run, the embedding model (~90 MB) is downloaded and cached automatically.

### Install as a global command

To run `tifo` from anywhere on your machine, install it as a standalone tool:

```bash
# Install the latest stable release directly from GitHub
uv tool install "git+https://github.com/Briant-s/file_renamer_organizer.git@stable"
```

This puts a `tifo` executable on your `PATH` (e.g. `~/.local/bin/tifo`). To pin an exact
release instead of tracking the branch, use a tag:

```bash
uv tool install "git+https://github.com/Briant-s/file_renamer_organizer.git@v0.2.0"
```

> [!TIP]
> Installing from a local clone works too: `uv tool install .`. After changing the source,
> reinstall with `uv tool install . --force` to pick up your changes.

> [!IMPORTANT]
> **TiFo runs fully offline by default.** On startup it sets `HF_HUB_OFFLINE` and
> `TRANSFORMERS_OFFLINE`, so the embedding model is loaded straight from the local
> HuggingFace cache with no network check on every run. Two assets must be present locally
> first:
>
> 1. The embedding model — cached automatically the first time you run TiFo _with_ a
>    network connection, or seed it manually:
>    ```bash
>    HF_HUB_OFFLINE=0 uv run python -c \
>      "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
>    ```
> 2. The LLM — pulled once via `ollama pull llama3.2:3b`.
>
> Once both are local, TiFo needs no internet. If the embedding model is missing from the
> cache, TiFo fails fast with an explicit message rather than hanging on a network call.

> [!TIP]
> On NVIDIA hardware you can opt into CUDA wheels for faster embedding. The project defines a
> `pytorch-cu124` index in `pyproject.toml` — point `torch` at it instead of the default CPU index.

## Usage

Running the tool starts an interactive prompt:

1. **Choose a folder** to organize (tab-completion supported).
2. **Pick a mode**:
   - _Rename Files Only_ — clean up names, keep the existing folder layout.
   - _Rename + Folder Organization_ — also sort files into folders.
3. **(Organize mode)** choose a folder strategy — manual names or by file type.
   Manual mode guides you toward clear, distinct folder names for better matching.
4. **Choose a naming format** — e.g. `Title Case` or `snake_case`.
5. **Review the preview** — a rename table or a folder tree.
6. **Confirm** — accept all, or cancel with no changes made.

Press `Ctrl+C` at any prompt to exit cleanly with no changes.

### Rename preview example

```
                 Rename Preview
┌──────────────────┬───┬────────────────────────────┐
│ Original         │   │ New Name                   │
├──────────────────┼───┼────────────────────────────┤
│ 3.txt            │ → │ Passwords & Credentials.txt│
│ 1.txt            │ → │ Weekly To-Do List.txt      │
│ 8.pdf            │ → │ Q3 Financial Summary.pdf   │
└──────────────────┴───┴────────────────────────────┘
```

In rename-only mode, files are renamed **where they already live** — a file in a subfolder
stays in that subfolder.

### Folder organization preview example

```
Folder Organization Preview
├── Documents  (3)
│   ├── Q3 Financial Summary.pdf
│   ├── Meeting Notes.docx
│   └── Project Plan.docx
├── Spreadsheets  (2)
│   ├── Budget 2026.xlsx
│   └── Expenses.csv
└── Unsorted  (1)
    └── app_idea_notes.txt
```

Folders are created inside the directory you selected, and low-confidence files land in
`Unsorted` rather than being forced into a poor match.

## Supported file types

| Category     | Extensions                                     | Extraction               |
| ------------ | ---------------------------------------------- | ------------------------ |
| Text         | `.txt`, `.md`, `.csv`, `.log`, and other UTF-8 | direct read              |
| PDF          | `.pdf`                                         | `pymupdf` text layer     |
| Word         | `.docx`                                        | `docx2txt`               |
| Spreadsheet  | `.xlsx`                                        | `openpyxl` cell values   |
| Other/binary | images, audio, video, archives, executables    | metadata + filename only |

> [!NOTE]
> Files with no extractable text still get classified using their filename and metadata,
> so nothing is silently dropped.

## Project structure

```
file_renamer/
├── pyproject.toml              # dependencies + the `tifo` entry point
└── tifo/
    ├── app.py                  # interactive entry point (forces offline HF mode)
    ├── common/
    │   ├── paths.py            # shared path helpers
    │   └── util.py             # prompt guards (graceful Ctrl+C handling)
    ├── embedding/
    │   ├── model.py            # embedder loader (device autodetect, offline, fallback)
    │   ├── expand_label.py     # folder-label expansion for better matching
    │   └── text_sampler.py     # sample builder for LLM context
    ├── naming/
    │   ├── generator.py        # LLM name generation
    │   └── formats.py          # naming-style formatters
    ├── classifiers/
    │   ├── base.py             # Classifier interface
    │   ├── manual.py           # semantic (embedding) classifier
    │   └── file_type.py        # extension-based classifier
    ├── extractors/
    │   ├── metadata.py         # filesystem metadata + text reading
    │   ├── pdf.py              # PDF extraction
    │   ├── docx.py             # Word extraction
    │   └── spreadsheet.py      # Excel extraction
    ├── pipeline/
    │   ├── no_clustering.py    # rename-only flow
    │   ├── with_clustering.py  # rename + organize flow
    │   ├── confirmation.py     # folder-tree preview
    │   └── resources.py        # model/LLM warm-up
    ├── renaming/
    │   └── renamer.py          # collision-safe move/rename
    └── ui/
        ├── display/            # banners, previews, feedback (rich)
        └── prompts/            # interactive prompts (questionary)
```

## Tech stack

| Layer              | Tool                                         |
| ------------------ | -------------------------------------------- |
| LLM backend        | Ollama + `llama3.2:3b`                       |
| Embeddings         | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| PDF / Word / Excel | `pymupdf`, `docx2txt`, `openpyxl`            |
| CLI UI             | `questionary` + `rich`                       |
| Compute            | `torch` (CPU by default, optional CUDA)      |
| Tooling            | `uv`, Python 3.13+                           |
