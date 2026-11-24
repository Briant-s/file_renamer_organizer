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

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **[Ollama](https://ollama.com)** installed and running
- The `qwen2.5:1b & qwen2.5:3b` model pulled locally

## Installation Steps

<details>
<summary><b>1. Install uv and Ollama</b></summary>

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://ollama.com/install.sh | sh   # Linux; on macOS, use the app from ollama.com/download
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Ollama: run the installer from https://ollama.com/download
```

Restart your terminal afterwards, then verify with `uv --version` and `ollama --version`.

</details>

```bash
# 2. Pull the models
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:3b

# 3. Install TiFo
uv tool install "git+https://github.com/Briant-s/file_renamer_organizer.git@stable"

# 4. Run
tifo        # CLI
tifo-gui    # GUI
```

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

## Supported file types

| Category     | Extensions                                          | Extraction                                    |
| ------------ | --------------------------------------------------- | --------------------------------------------- |
| Text         | `.txt`, `.log`, `.csv`                              | direct read                                   |
| Markdown     | `.md`                                               | direct read                                   |
| PDF          | `.pdf`                                              | `pymupdf` text layer                          |
| Word         | `.docx`                                             | `docx2txt`                                    |
| Spreadsheet  | `.xlsx`                                             | `openpyxl` cell values                        |
| PowerPoint   | `.pptx`                                             | `python-pptx` slide text                      |
| Archives     | `.zip`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.xz`, `.7z` | archive contents listing                      |
| Images       | common image formats                                | EXIF metadata + filename (no visual analysis) |
| Other/binary | audio, video, executables                           | metadata + filename only                      |
