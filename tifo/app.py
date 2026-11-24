import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from rich.console import Console

from tifo.common.util import require

from tifo.ui.display.banners import welcome_banner, renaming_banner, clustering_banner
from tifo.ui.prompts.main_menu import (
    prompt_language,
    prompt_main_path,
    prompt_mode,
    prompt_clustering_strat,
    prompt_describe_or_reformat,
)

from tifo.extractors.metadata import extract_contents

from tifo.pipeline.with_clustering import get_folder_names, with_clustering_pipeline

from tifo.naming.formats import prompt_naming_format
from tifo.pipeline.resources import load_resources
from tifo.pipeline.no_clustering import renaming_pipeline

from tifo.setup import ensure_embedder, setup_complete


def _run():
    welcome_banner()

    # First-run setup: the app runs offline, so the embedding model must be in
    # the local cache before any mode loads it. On a fresh install we download
    # it once (needs network); later runs skip this via the setup marker.
    if not setup_complete():
        if not ensure_embedder():
            Console().print(
                "[red]Setup is required before TiFo can run. Exiting.[/red]"
            )
            raise SystemExit(1)

    language_chosen = require(prompt_language())
    DIR_PATH = require(prompt_main_path())
    mode_choice = require(prompt_mode())
    
    if mode_choice == "rename_only":
        renaming_banner(DIR_PATH)
        
        label, formatter = require(prompt_naming_format())
        use_date = "YYYY-MM-DD" in label

        # Ask whether to describe from content (LLM) or just reformat names.
        describe = prompt_describe_or_reformat()

        # loading — only warm the LLM when we actually describe from content.
        raw_files = extract_contents(root_path=DIR_PATH)
        res = load_resources(needs_embedder=False, needs_llm=describe)

        renaming_pipeline(formatter=formatter, use_date=use_date, describe=describe, raw_files=raw_files, root_dir=DIR_PATH)
        
    elif mode_choice == "clustering":
        strat_choice = require(prompt_clustering_strat())
        clustering_banner(strat_choice, DIR_PATH)
        
        # if manual folder names
        manual_labels = get_folder_names() if "manual" in strat_choice else None

        # loading
        raw_files = extract_contents(root_path=DIR_PATH)
        needs_ai = strat_choice in ("manual", "auto_organize")
        res = load_resources(needs_embedder=needs_ai, needs_llm=needs_ai)
        
        with_clustering_pipeline(
            strat_choice=strat_choice,
            raw_files=raw_files,
            folder_labels=manual_labels,
            res=res,
            root_dir=DIR_PATH
            )

def run_app():
    try:
        _run()
    except KeyboardInterrupt:
        Console().print("\n[dim]Exiting TiFo. No changes were made.[/dim]")
        raise SystemExit(0)

    
    
if __name__ == "__main__":
    run_app()