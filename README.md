<div align="center">

# TiFo

**Rename and organize your files by their actual content — locally, privately, offline.**

</div>

TiFo is a command-line tool that reads what your files are *about* and gives them clean,
descriptive names, then sorts them into folders that make sense. It runs entirely on your
machine using a local LLM (via [Ollama](https://ollama.com)) and local embeddings — no
cloud, no API keys, nothing leaves your computer.

Point it at a folder of messy files like `1.txt`, `report(final)(2).docx`, or `IMG_4821.pdf`,
and get back `Weekly To-Do List.txt`, `Q3 Financial Summary.docx`, and a tidy folder tree.

> [!NOTE]
> TiFo works on **non-destructive copies by default** — your originals are never touched.
> Organized files are written to a separate output directory so you can review before committing.

## Features

- **Content-aware renaming** — extracts text from each file and asks a local LLM for a short,
  specific title (e.g. `Grocery Shopping List`, not `Text Document`).
- **Multi-format extraction** — plain text, Markdown, CSV, logs, PDF, Word (`.docx`), and Excel (`.xlsx`).
  Binary and unreadable files are handled gracefully.
- **Two workflows** — rename files in place, or rename *and* organize them into folders.
- **Three folder strategies**:
  - *Manual + semantic* — you name the folders, TiFo places files using embedding similarity.
  - *By file type* — sorts into `Documents`, `Images`, `Spreadsheets`, `Code`, and more.
  - *Auto organize* — planned, not yet available.
- **Flexible naming formats** — `Title Case`, `snake_case`, `kebab-case`, `lowercase`,
  `UPPERCASE`, plus date-prefixed variants (`YYYY-MM-DD ...`).
- **Preview before applying** — see a diff-style rename table or a folder tree, then accept or cancel.
- **Safe by design** — collision-safe deduplication, an explicit `Unsorted` bucket for
  low-confidence matches, and path-escape guards.
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
  ┌───────────────┐    diff/tree preview → your confirmation → copy into place
  │  Preview +    │
  │  Apply        │
  └───────────────┘
```

- **Embeddings** use `sentence-transformers` with the `all-MiniLM-L6-v2` model.
- **Naming and label expansion** use the `llama3.2:3b` model through Ollama.
- For folder classification, labels are expanded into richer descriptions before embedding,
  and low-confidence files (below threshold or with a close top-2 gap) are routed to `Unsorted`.

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **[Ollama](https://ollama.com)** installed and running
- The `llama3.2:3b` model pulled locally

## Getting started

```bash
# 1. Install dependencies (CPU wheels by default)
uv sync

# 2. Pull the LLM model
ollama pull llama3.2:3b

# 3. Run
uv run main.py
```

On first run, the embedding model (~90 MB) is downloaded and cached automatically.

> [!TIP]
> On NVIDIA hardware you can opt into CUDA wheels for faster embedding. The project defines a
> `pytorch-cu124` index in `pyproject.toml` — point `torch` at it instead of the default CPU index.

## Usage

Running the tool starts an interactive prompt:

1. **Choose a folder** to organize (tab-completion supported).
2. **Pick a mode**:
   - *Rename Files Only* — clean up names, keep the folder layout.
   - *Rename + Folder Organization* — also sort files into folders.
3. **(Organize mode)** choose a folder strategy — manual names or by file type.
4. **Choose a naming format** — e.g. `Title Case` or `snake_case`.
5. **Review the preview** — a rename table or a folder tree.
6. **Confirm** — accept all, or cancel with no changes made.

### Rename preview example

```
                 Rename Preview
┌──────────────────┬───┬───────────────────────────┐
│ Original         │   │ New Name                  │
├──────────────────┼───┼───────────────────────────┤
│ 3.txt            │ → │ Passwords & Credentials.txt│
│ 1.txt            │ → │ Weekly To-Do List.txt     │
│ 8.pdf            │ → │ Q3 Financial Summary.pdf  │
└──────────────────┴───┴───────────────────────────┘
```

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

## Supported file types

| Category      | Extensions                                   | Extraction              |
| ------------- | -------------------------------------------- | ----------------------- |
| Text          | `.txt`, `.md`, `.csv`, `.log`, and other UTF-8 | direct read             |
| PDF           | `.pdf`                                        | `pymupdf` text layer    |
| Word          | `.docx`                                        | `docx2txt`              |
| Spreadsheet   | `.xlsx`                                        | `openpyxl` cell values  |
| Other/binary  | images, audio, video, archives, executables   | metadata + filename only |

> [!NOTE]
> Files with no extractable text still get classified using their filename and metadata,
> so nothing is silently dropped.

## Project structure

```
file_renamer/
├── main.py                     # interactive entry point
├── pyproject.toml
└── src/
    ├── app.py                  # alternate app runner (banners, language, formats)
    ├── clustering_flow.py      # embedding prep + similarity helpers
    ├── ai/
    │   ├── model.py            # embedder loader (device autodetect + fallback)
    │   ├── generator.py        # LLM name generation
    │   ├── expand_label.py     # folder-label expansion for better matching
    │   └── text_sampler.py     # sample builder for LLM context
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
    └── utils/
        ├── renamer.py          # collision-safe copy/move/rename
        ├── naming_formats.py   # naming-style formatters
        ├── comparison.py       # rename diff table
        └── gui/                # prompts, banners, reactions (rich + questionary)
```

## Tech stack

| Layer        | Tool                                              |
| ------------ | ------------------------------------------------- |
| LLM backend  | Ollama + `llama3.2:3b`                             |
| Embeddings   | `sentence-transformers` (`all-MiniLM-L6-v2`)      |
| PDF / Word / Excel | `pymupdf`, `docx2txt`, `openpyxl`           |
| CLI UI       | `questionary` + `rich`                            |
| Compute      | `torch` (CPU by default, optional CUDA)           |
| Tooling      | `uv`, Python 3.13+                                 |
