# App Flow & Refactor Plan

> Reference for the AI File Renamer & Organizer pipeline flow and the UI/pipeline refactor.

---

## Core Principles

1. **Prompts first, loading last.** Gather *all* user decisions before touching any model, extraction, or LLM.
2. **Load only what's needed.** Each pipeline loads exactly the resources its chosen path requires — nothing more.
3. **UI lives in `gui/`.** Logic files (pipelines, renamer, clustering) hold no prompts or result-rendering.
4. **Confirm + show results** whenever folders are created or files are renamed.

---

## Overall Flow

```
[1] Language prompt            (English now; Indonesian LAST — skip for now, scaffold only)
        |
[2] Working directory prompt
        |
[3] Mode prompt: Renaming Only | With Clustering
        |
        ├─ RENAMING ONLY
        │     → naming-format prompt
        │     → (load LLM) extract + generate names
        │     → preview comparison → confirm → show results
        │
        └─ WITH CLUSTERING
              → clustering-strategy prompt:
                    (a) manually write folder names
                    (b) cluster by file type      (no embedder)
                    (c) auto-generate names + classification  (needs embedder)
              → "Rename files too, or classification only?"   ← key decision
                    ├─ classification only → skip naming format, skip name generation
                    └─ rename too          → naming-format prompt
              ── end of prompts ──
              → load ONLY what this path needs (see matrix below)
              → create folders  → confirm + show results
              → move / rename    → confirm + show results
```

---

## What Each Path Loads (embedder / LLM gating)

| Strategy | Rename? | Embedder | LLM (name gen) |
|---|---|---|---|
| manual folder names | classification only | ❌ | ❌ |
| manual folder names | rename too | ❌ | ✅ |
| by file type | classification only | ❌ | ❌ |
| by file type | rename too | ❌ | ✅ |
| auto-generate | classification only | ✅ | ✅ (label expansion) |
| auto-generate | rename too | ✅ | ✅ |
| (rename-only mode) | always renames | ❌ | ✅ |

> The "Rename vs classification only" prompt is the last decision — it lets you compute the minimal load set before loading anything.

---

## Cross-Cutting Rules

- **Any path that renames files** → must show the naming-format prompt.
- **Any path that creates folders** → confirm before + show results table after.
- **Any path that renames files** → preview comparison + confirm + show results table.

---

## Target `gui/` Layout (under `src/utils/gui/`)

Keep UI cohesive and out of logic files. Proposed split (finalize while refactoring):

| File | Responsibility |
|---|---|
| `prompts.py` | Input prompts: working dir, mode menu, naming format, clustering strategy, rename-vs-classify, confirmations |
| `results.py` | Output rendering: rename comparison preview, rename results table, folder-creation results table |
| `folders_gui.py` | Folder-name collection (already exists) |

Logic stays put:
- `naming_formats.py` keeps `NAMING_FORMATS` dict + `apply_naming_format()` (gui imports the dict).
- `renamer.py` keeps `rename()` / `rename_flow()` (UI moves to `gui/results.py`).
- `comparison.py` UI (`compare_results`) moves into `gui/results.py`.

---

## Refactor To-Do (17 tasks)

**UI extraction groundwork**
1. Inventory all UI touchpoints
2. Design `gui/` module layout, separate UI from logic
3. Move path + main menu prompts out of `main.py`
4. Move naming-format prompt into gui (keep formatter logic behind)
5. Move comparison + rename-results UI into gui
6. Consolidate duplicate `get_folder_names` into `gui/folders_gui.py`
7. Reorder `main.py`: gather all user info BEFORE model loading
8. Each pipeline loads what it requires (self-loading, not passed in)
9. Update imports across `main.py` and pipelines
10. Verify end-to-end for both branches

**New flow additions**
11. Language selection prompt (English now, Indonesian LAST — skip for now)
12. Clustering strategy sub-menu (manual / by file type / auto-generate)
13. Implement "cluster by file type" grouping path (no model)
14. Wire naming-format prompt into every path that renames
15. Confirm + results UI for folder creation step
16. Gate embedder loading to only the auto-generate path
17. "Rename + classify" vs "classification only" prompt in clustering info-gathering phase

---

## Known Cleanups Along the Way

- `clustering_flow.py` `get_folder_names()` uses raw `input()` → delete, use `gui/folders_gui.py`.
- `with_clustering.py` has a duplicate `get_folder_names()` and a buggy `create_directory` / `directory_flow`:
  - `root` param is accepted but never joined.
  - `mkdir()` missing `parents=True`.
  - `directory_flow` calls `create_directory(d)` with wrong arg count, has stray empty backticks, and returns nothing.
  - Fix: single shared `create_directory(dir_name, root, allow_existing)` helper using `Path(root) / dir_name` + `mkdir(parents=True, ...)`.
- `main.py` currently loads the embedder + extracts contents BEFORE the menu → move into the branch that needs it.
