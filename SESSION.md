# Demo Session — Task Tracker

> Goal: end-to-end working prototype by end of session
> Flow: drop files in → extract content → suggest name → classify into folder → preview → confirm

---

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1 — Extractors

Install packages first:

```bash
uv add pymupdf python-docx openpyxl Pillow
```

| Task                               | File                            | Package                        | Status |
| ---------------------------------- | ------------------------------- | ------------------------------ | ------ |
| Pydantic return model              | `src/extractors/models.py`      | `pydantic` (already installed) | [x]    |
| PDF extraction                     | `src/extractors/pdf.py`         | `pymupdf`                      | [x]    |
| Word doc extraction                | `src/extractors/docx.py`        | `python-docx`                  | [x]    |
| Spreadsheet extraction             | `src/extractors/spreadsheet.py` | `openpyxl`                     | [x]    |
| Image metadata                     | `src/extractors/image.py`       | `Pillow`                       | [ ]    |
| Wire extractors into `metadata.py` | `src/extractors/metadata.py`    | —                              | [x]    |

### What "wire into metadata.py" means

In `extract_contents()`, after the existing `_read_text_safe()` call, add a dispatcher:

```python
if suffix == ".pdf":
    result = extract_pdf(entry)
elif suffix == ".docx":
    result = extract_docx(entry)
elif suffix in (".xlsx",):
    result = extract_spreadsheet(entry)
elif suffix in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
    result = extract_image(entry)
else:
    result = ExtractedFile(content=content, metadata={})

# then use result.content and result.metadata in the dict
```

---

## Phase 2 — Smarter Name Generation

| Task                             | File                  | Notes                                  | Status |
| -------------------------------- | --------------------- | -------------------------------------- | ------ |
| Fix hardcoded `.txt` extension   | `src/ai/generator.py` | Preserve original file extension       | [x]    |
| Truncate content before LLM call | `src/ai/generator.py` | Cap at ~1000 chars, same as clustering | [x]    |
| Title Case output                | `src/ai/generator.py` | Add format instruction to prompt       | [x]    |

---

## Phase 4 — Preview & Confirmation UI

| Task                        | File                   | Notes                                  | Status |
| --------------------------- | ---------------------- | -------------------------------------- | ------ |
| Build preview table         | `src/utils/preview.py` | Show `[Rename] old.pdf → New Name.pdf` | [x]    |
| Accept all / Reject all     | `src/utils/preview.py` | Simple y/n prompt                      | [ ]    |
| Wire preview into main flow | `main.py`              | Call preview before applying renames   | [ ]    |

---

## Wiring — Connect Everything in main.py

End-to-end flow to stitch together:

```
extract_contents()         # metadata.py — now with real content for PDFs, DOCX, images
    ↓
generate_name()            # generator.py — per file, uses content
    ↓
clustering_flow()          # clustering_flow.py — classify into user-defined folders
    ↓
preview()                  # preview.py — show diff, ask for confirmation
    ↓
rename() + move()          # renamer.py — apply changes
```

| Task                                                             | Status |
| ---------------------------------------------------------------- | ------ |
| Pass extracted content into `generate_name()` for all file types | [ ]    |
| Show preview before applying any changes                         | [ ]    |
| Apply confirmed renames and moves                                | [ ]    |

---

## Things to defer (not today)

- Audio/video transcription (Whisper) — too slow, too complex
- OCR for scanned PDFs — skip, `content=None` fallback handles it
- Phase 3 threshold tuning — current classifier is good enough for demo files
- Phase 5 cross-platform / packaging
- Phase 6 config file
- `FileRecord` Pydantic model refactor — do after demo

---

## Demo Script

1. Prepare a folder with: 1 PDF, 1 DOCX, 1 XLSX, 1-2 images, 1-2 plain text files
2. Run the tool
3. Enter 3-4 folder names when prompted (e.g. "School Notes", "Finance", "Personal")
4. Show the preview table
5. Confirm → files renamed and moved
