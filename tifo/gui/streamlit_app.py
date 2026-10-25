"""TiFo Streamlit GUI.

A browser frontend over :mod:`tifo.core`. It mirrors the CLI
(:mod:`tifo.app`) step for step — same ordered choices, same wording, same
guidance — but renders each step as Streamlit widgets instead of
rich/questionary.

CLI step order being mirrored:

  Rename-only:
    1. Language  -> 2. Folder  -> 3. Mode  -> 4. Naming format
    -> 5. Rename preview -> 6. Confirm (Accept All / Cancel) -> results

  Rename + organize:
    1. Language  -> 2. Folder  -> 3. Mode  -> 4. Folder strategy
    -> 4b. (manual) folder names  -> 5. Folder-tree preview
    -> 6. Confirm (Accept All / Cancel)
    -> 7. How to place (Move only / Rename + move)
    -> 7b. (rename) Naming format -> results

Run via the ``tifo-gui`` console script, or directly:
``streamlit run tifo/gui/streamlit_app.py``.
"""

from __future__ import annotations

# Force offline HuggingFace mode BEFORE importing anything that may pull the
# embedding stack — identical to tifo/app.py so GUI and CLI behave the same.
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from collections import defaultdict
from pathlib import Path

import streamlit as st

from tifo.extractors.metadata import extract_contents
from tifo.naming.formats import NAMING_FORMATS
from tifo.pipeline.resources import load_resources
from tifo.common.recent import add_recent, load_recent

from tifo.core.rename_service import RenamePlan, apply_renames, plan_renames
from tifo.core.organize_service import (
    OrganizePlan,
    apply_organization,
    plan_organization,
    resolve_target_names,
)

# --------------------------------------------------------------------------- #
# Brand assets (logo + favicon)
# --------------------------------------------------------------------------- #
# Logo/icon files live in tifo/gui/assets/ so they ship inside the wheel. All
# are optional: missing files fall back gracefully (emoji tab icon, no logo).
_ASSETS = Path(__file__).resolve().parent / "assets"


def _asset(name: str) -> str | None:
    """Return the path to an asset file if it exists, else None."""
    candidate = _ASSETS / name
    return str(candidate) if candidate.is_file() else None


# Favicon: use the brand icon if present, otherwise the 📁 emoji.
_FAVICON = _asset("favicon.png") or _asset("logo_small.png") or "📁"
st.set_page_config(page_title="TiFo", page_icon=_FAVICON, layout="centered")

# Persistent logo in the top-left / sidebar (Streamlit >= 1.35). Only call it
# when a logo file is actually present so we don't error on a bare checkout.
_LOGO = _asset("logo.png") or _asset("logo.svg")
if _LOGO:
    try:
        st.logo(_LOGO, icon_image=_asset("logo_small.png") or _LOGO)
    except Exception:
        # Older Streamlit without st.logo — ignore, the title banner still shows.
        pass


# --------------------------------------------------------------------------- #
# Wizard state
# --------------------------------------------------------------------------- #
# A single linear flow, like the CLI. ``step`` names the stage we are on; the
# user's answers accumulate in ``st.session_state`` as they advance.
STEPS_RENAME = ["language", "folder", "mode", "format", "confirm", "preview", "results"]
STEPS_ORGANIZE = [
    "language", "folder", "mode", "strategy", "folder_names",
    "confirm", "preview", "place", "format", "results",
]


def _init() -> None:
    st.session_state.setdefault("step", "language")


def _go(step: str) -> None:
    st.session_state.step = step
    st.rerun()


def _restart() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.step = "language"
    st.rerun()


def _on(step: str) -> bool:
    return st.session_state.get("step") == step


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _progress_callback(label: str):
    bar = st.progress(0.0, text=label)

    def _cb(done: int, total: int) -> None:
        bar.progress(done / total if total else 1.0, text=f"{label} ({done}/{total})")

    return _cb


def _group_by_folder(results: list[dict]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for f in results:
        buckets[f.get("matching_folder") or "Unsorted"].append(f["file_name"])
    return buckets


def _list_children(path: str, limit: int = 60):
    """List immediate children of a folder (folders first, then files).

    Returns ``(rows, n_folders, n_files, truncated)`` where ``rows`` is a list
    of ``{"Type", "Name"}`` dicts. One level only — fast (``os.scandir``) and
    just a sanity check so the user confirms the right folder before the heavy
    recursive extraction runs.
    """
    folders, files = [], []
    try:
        with os.scandir(Path(path).expanduser()) as it:
            for entry in it:
                try:
                    is_dir = entry.is_dir()
                except OSError:
                    is_dir = False
                (folders if is_dir else files).append(entry.name)
    except (PermissionError, OSError):
        return [], 0, 0, False

    folders.sort(key=str.lower)
    files.sort(key=str.lower)
    n_folders, n_files = len(folders), len(files)

    rows = (
        [{"Type": "📁 folder", "Name": n} for n in folders]
        + [{"Type": "📄 file", "Name": n} for n in files]
    )
    truncated = len(rows) > limit
    return rows[:limit], n_folders, n_files, truncated


def _folder_is_valid(path: str) -> bool:
    return bool(path) and Path(path).expanduser().is_dir()


def _show_outcome(outcome) -> None:
    st.success(
        f"{len(outcome.renamed)} applied · "
        f"{len(outcome.skipped)} skipped · "
        f"{len(outcome.failed)} failed"
    )
    if outcome.renamed:
        st.markdown("**Applied**")
        st.table({"File": [o for o, _ in outcome.renamed],
                  "Detail": [d for _, d in outcome.renamed]})
    if outcome.skipped:
        st.markdown("**Skipped**")
        st.table({"File": [o for o, _ in outcome.skipped],
                  "Reason": [d for _, d in outcome.skipped]})
    if outcome.failed:
        st.markdown("**Failed**")
        st.table({"File": [o for o, _ in outcome.failed],
                  "Reason": [d for _, d in outcome.failed]})


# --------------------------------------------------------------------------- #
# Header + progress rail (shows where you are, like the CLI banners)
# --------------------------------------------------------------------------- #
_init()

if _LOGO:
    st.image(_LOGO, width=220)
else:
    st.title("📁 TiFo")
st.caption("Rename & organize files by their content — local, private, offline.")

_mode = st.session_state.get("mode")
_steps = STEPS_ORGANIZE if _mode == "clustering" else STEPS_RENAME
_labels = {
    "language": "Language",
    "folder": "Folder",
    "mode": "Mode",
    "strategy": "Strategy",
    "folder_names": "Folder names",
    "format": "Naming format",
    "confirm": "Confirm",
    "preview": "Preview",
    "place": "Placement",
    "results": "Results",
}
_current = st.session_state.get("step", "language")
if _current in _steps:
    _idx = _steps.index(_current)
    trail = "  ›  ".join(
        f"**{_labels[s]}**" if i == _idx else _labels[s]
        for i, s in enumerate(_steps)
    )
    st.caption(trail)
st.divider()


# --------------------------------------------------------------------------- #
# Step 1 — Language  (parity with prompt_language; English only for now)
# --------------------------------------------------------------------------- #
if _on("language"):
    st.subheader("Select Language")
    lang = st.selectbox("Language", options=["English (Default)"], index=0)
    st.caption("Indonesian is not available yet.")
    if st.button("Continue", type="primary"):
        st.session_state.language = "eng"
        _go("folder")


# --------------------------------------------------------------------------- #
# Step 2 — Folder path  (parity with prompt_main_path)
# --------------------------------------------------------------------------- #
elif _on("folder"):
    st.subheader("Choose a folder")

    with st.expander("How do I copy a folder path?"):
        st.markdown(
            "- **Windows:** in File Explorer, hold **Shift**, right-click the "
            "folder, and choose **Copy as path**. Remove the surrounding quotes "
            "if present.\n"
            "- **macOS:** right-click the folder, hold **Option**, and choose "
            "**Copy “…” as Pathname**. Or drag the folder into a Terminal window.\n"
            "- **Linux:** in most file managers, right-click → **Copy** then paste, "
            "or use the path shown in the location bar (press **Ctrl+L** to reveal it)."
        )

    # Recent folders (persisted across runs). Picking one fills the input below.
    _recent = load_recent()
    if _recent:
        def _use_recent() -> None:
            chosen = st.session_state.get("recent_pick")
            if chosen and chosen != "—":
                st.session_state.folder_input = chosen

        st.selectbox(
            "Recent folders",
            options=["—", *_recent],
            key="recent_pick",
            on_change=_use_recent,
            help="Folders you've used before. Selecting one fills the path below.",
        )

    st.session_state.setdefault("folder_input", st.session_state.get("folder", ""))
    folder = st.text_input(
        "Enter folder path to organize",
        key="folder_input",
        placeholder="/home/you/Downloads/messy_folder",
    )

    if folder and not _folder_is_valid(folder):
        st.error("That path is not an existing folder.")
    elif folder:
        # Show the folder's immediate contents so the user can confirm it's the
        # right one BEFORE the expensive recursive extraction runs.
        rows, n_folders, n_files, truncated = _list_children(folder)
        st.caption(
            f"Contents: {n_folders} folder(s), {n_files} file(s) "
            "(top level only)"
        )
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True, height=240)
            if truncated:
                st.caption("…and more not shown.")
        else:
            st.caption("This folder is empty, or its contents can't be read.")

    col_back, _spacer, col_next = st.columns([1, 4, 1])
    if col_back.button("Back"):
        _go("language")
    if col_next.button("Continue", type="primary", disabled=not _folder_is_valid(folder)):
        resolved = str(Path(folder).expanduser())
        st.session_state.folder = resolved
        add_recent(resolved)  # persist for next time
        _go("mode")


# --------------------------------------------------------------------------- #
# Step 3 — Mode  (parity with prompt_mode)
# --------------------------------------------------------------------------- #
elif _on("mode"):
    st.subheader("Select pipeline")
    mode = st.radio(
        "Mode",
        options=["rename_only", "clustering"],
        format_func=lambda m: (
            "Rename Files Only" if m == "rename_only" else "Rename + Folder Organization"
        ),
        index=0 if st.session_state.get("mode", "rename_only") == "rename_only" else 1,
        label_visibility="collapsed",
    )
    st.caption(
        "Rename Files Only cleans up names and keeps the existing layout. "
        "Rename + Folder Organization also sorts files into folders."
    )
    col_back, _spacer, col_next = st.columns([1, 4, 1])
    if col_back.button("Back"):
        _go("folder")
    if col_next.button("Continue", type="primary"):
        st.session_state.mode = mode
        _go("format" if mode == "rename_only" else "strategy")


# --------------------------------------------------------------------------- #
# Step 4 (rename-only) — Naming format  (parity with prompt_naming_format)
# --------------------------------------------------------------------------- #
elif _on("format") and st.session_state.get("mode") == "rename_only":
    st.subheader("Choose a naming format")
    example = "quarterly budget report"
    fmt_label = st.radio(
        "Naming format",
        options=list(NAMING_FORMATS.keys()),
        format_func=lambda lbl: f"{lbl}  →  '{NAMING_FORMATS[lbl](example)}'",
        label_visibility="collapsed",
    )
    col_back, col_next = st.columns(2)
    if col_back.button("Back"):
        _go("mode")
    if col_next.button("Continue", type="primary"):
        st.session_state.fmt_label = fmt_label
        # No heavy work here — the summary/confirm step owns extraction + load.
        _go("confirm")


# --------------------------------------------------------------------------- #
# Step 4 (organize) — Folder strategy  (parity with prompt_clustering_strat)
# --------------------------------------------------------------------------- #
elif _on("strategy"):
    st.subheader("Select folder strategy")
    strat = st.radio(
        "Strategy",
        options=["manual", "file_based"],
        format_func=lambda s: (
            "Manually Write Folder Names" if s == "manual" else "Organize by File Type"
        ),
        label_visibility="collapsed",
    )
    col_back, _spacer, col_next = st.columns([1, 4, 1])
    if col_back.button("Back"):
        _go("mode")
    if col_next.button("Continue", type="primary"):
        st.session_state.strat_choice = strat
        _go("folder_names" if strat == "manual" else "confirm")


# --------------------------------------------------------------------------- #
# Step 4b (organize, manual) — Folder names  (parity with get_folder_names)
# --------------------------------------------------------------------------- #
elif _on("folder_names"):
    st.subheader("Name the folders")
    st.info(
        "TiFo matches each file to the **closest folder by meaning**, so use "
        "**specific, distinct** labels (Documentation, Task Lists, Financial "
        "Reports) rather than vague ones (Misc, Stuff). Add **2+** folders; "
        "low-confidence files go to **Unsorted**.",
        icon="💡",
    )
    labels_raw = st.text_area(
        "Folder names (one per line)",
        value=st.session_state.get("folder_labels_raw", ""),
        placeholder="Documents\nFinancial Reports\nTask Lists",
        height=140,
    )
    labels = [ln.strip() for ln in labels_raw.splitlines() if ln.strip()]
    # Case-insensitive de-dup, preserving order (parity with validate_folder).
    seen: set[str] = set()
    deduped: list[str] = []
    for lbl in labels:
        if lbl.lower() not in seen:
            seen.add(lbl.lower())
            deduped.append(lbl)
    labels = deduped

    if labels:
        st.caption("  ·  ".join(labels))
    if len(labels) == 1:
        st.warning(
            "You added only **one folder**. With a single folder there's nothing "
            "to compare against — files will either go into it or land in "
            "**Unsorted**.",
            icon="⚠️",
        )

    col_back, _spacer, col_next = st.columns([1, 4, 1])
    if col_back.button("Back"):
        _go("strategy")
    if col_next.button("Continue", type="primary", disabled=not labels):
        st.session_state.folder_labels_raw = labels_raw
        st.session_state.folder_labels = labels
        _go("confirm")


# --------------------------------------------------------------------------- #
# Confirm step — summary of every choice, then the heavy work runs behind the
# primary button. Shared by both flows: nothing expensive happens until the
# user clicks "Start".
# --------------------------------------------------------------------------- #
elif _on("confirm"):
    mode = st.session_state.get("mode")
    st.subheader("Review and start")

    folder = st.session_state.get("folder", "")
    st.markdown(f"**Folder to process**\n\n`{folder}`")

    # Summary rows common + mode-specific.
    if mode == "rename_only":
        st.markdown(
            f"**Mode:** Rename files only  \n"
            f"**Naming format:** {st.session_state.get('fmt_label')}"
        )
        back_target = "format"
    else:
        strat = st.session_state.get("strat_choice")
        strat_label = (
            "Manually Write Folder Names" if strat == "manual" else "Organize by File Type"
        )
        st.markdown(
            f"**Mode:** Rename + folder organization  \n"
            f"**Folder strategy:** {strat_label}"
        )
        if strat == "manual":
            labels = st.session_state.get("folder_labels") or []
            st.markdown("**Folders:** " + ("  ·  ".join(labels) if labels else "—"))
        back_target = "folder_names" if strat == "manual" else "strategy"

    st.caption(
        "Starting will read the files in this folder and load the local model. "
        "This can take a moment for large folders. No files are changed yet — "
        "you'll still see a preview and confirm before anything is renamed."
    )

    col_back, _spacer, col_next = st.columns([1, 4, 1])
    if col_back.button("Back"):
        _go(back_target)
    if col_next.button("Start", type="primary"):
        if mode == "rename_only":
            with st.spinner("Extracting file contents..."):
                raw_files = extract_contents(
                    root_path=folder, show_progress=False
                )
                load_resources(needs_embedder=False, needs_llm=True, quiet=True)
            fmt_label = st.session_state.get("fmt_label")
            plan = plan_renames(
                formatter=NAMING_FORMATS[fmt_label],
                use_date="YYYY-MM-DD" in fmt_label,
                raw_files=raw_files,
                on_progress=_progress_callback("Generating file names"),
            )
            st.session_state.rename_plan = plan
        else:
            strat = st.session_state.strat_choice
            needs_ai = strat == "manual"
            with st.spinner("Extracting file contents and classifying..."):
                raw_files = extract_contents(root_path=folder, show_progress=False)
                res = load_resources(needs_embedder=needs_ai, needs_llm=needs_ai, quiet=True)
                plan = plan_organization(
                    strat_choice=strat,
                    raw_files=raw_files,
                    folder_labels=st.session_state.get("folder_labels"),
                    embedder=res.embedder,
                    root_dir=folder,
                )
            st.session_state.organize_plan = plan
        _go("preview")


# --------------------------------------------------------------------------- #
# Step 5/6 — Preview + Confirm  (parity with compare_results / preview_folders
# + prompt_rename_option, including the red destructive warning)
# --------------------------------------------------------------------------- #
elif _on("preview"):
    mode = st.session_state.get("mode")

    if mode == "rename_only":
        st.subheader("Rename Preview")
        plan: RenamePlan = st.session_state.rename_plan
        st.dataframe(
            {"Original": plan.old_names, "New Name": plan.new_names},
            width="stretch",
            hide_index=True,
        )
        confirm_label = "Apply Current Renames?"
    else:
        st.subheader("Folder Organization Preview")
        plan: OrganizePlan = st.session_state.organize_plan
        buckets = _group_by_folder(plan.results)
        for folder_name in sorted(buckets, key=lambda n: (n == "Unsorted", n.lower())):
            files = sorted(buckets[folder_name])
            with st.expander(f"{folder_name}  ({len(files)})", expanded=True):
                for name in files:
                    st.write(f"• {name}")
        confirm_label = "Apply Current Folder Options?"

    st.error(
        "Files in the selected folder will be **renamed/moved in place**. "
        "This **cannot be undone**. Make sure you have a backup if unsure.",
        icon="⚠️",
    )

    st.write(confirm_label)
    col_cancel, _spacer, col_accept = st.columns([1, 4, 1])
    cancel = col_cancel.button("Cancel")
    accept = col_accept.button("Accept All", type="primary")

    if cancel:
        st.info("No changes were made.")
        if st.button("Start over"):
            _restart()
    elif accept:
        if mode == "rename_only":
            st.session_state.outcome = apply_renames(st.session_state.rename_plan)
            _go("results")
        else:
            # Organize: confirmed the tree; next decide placement (CLI step 7).
            _go("place")


# --------------------------------------------------------------------------- #
# Step 7 (organize) — How to place  (parity with prompt_rename_or_move)
# --------------------------------------------------------------------------- #
elif _on("place"):
    st.subheader("How should files be placed into folders?")
    placement = st.radio(
        "Placement",
        options=["move", "rename"],
        format_func=lambda p: (
            "Move only (keep names, fast)" if p == "move"
            else "Rename + move (AI names, slower)"
        ),
        label_visibility="collapsed",
    )
    col_back, col_next = st.columns(2)
    if col_back.button("Back"):
        _go("preview")
    if col_next.button("Continue", type="primary"):
        st.session_state.placement = placement
        if placement == "rename":
            _go("format")  # organize + rename needs a naming format next
        else:
            plan: OrganizePlan = st.session_state.organize_plan
            new_names = resolve_target_names(plan, rename_too=False)
            st.session_state.outcome = apply_organization(plan, new_names)
            _go("results")


# --------------------------------------------------------------------------- #
# Step 7b (organize + rename) — Naming format, then apply
# --------------------------------------------------------------------------- #
elif _on("format") and st.session_state.get("mode") == "clustering":
    st.subheader("Choose a naming format")
    example = "quarterly budget report"
    fmt_label = st.radio(
        "Naming format",
        options=list(NAMING_FORMATS.keys()),
        format_func=lambda lbl: f"{lbl}  →  '{NAMING_FORMATS[lbl](example)}'",
        label_visibility="collapsed",
    )
    col_back, col_next = st.columns(2)
    if col_back.button("Back"):
        _go("place")
    if col_next.button("Apply", type="primary"):
        plan: OrganizePlan = st.session_state.organize_plan
        new_names = resolve_target_names(
            plan,
            rename_too=True,
            formatter=NAMING_FORMATS[fmt_label],
            use_date="YYYY-MM-DD" in fmt_label,
            on_progress=_progress_callback("Generating file names"),
        )
        st.session_state.outcome = apply_organization(plan, new_names)
        _go("results")


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #
elif _on("results"):
    st.subheader("Rename Results")
    _show_outcome(st.session_state.outcome)
    st.caption(f"Files are here: {Path(st.session_state.folder).resolve()}")
    if st.button("Start over", type="primary"):
        _restart()
