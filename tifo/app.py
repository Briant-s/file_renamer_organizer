import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from tifo.ui.display.banners import welcome_banner, renaming_banner, clustering_banner
from tifo.ui.prompts.main_menu import (
    prompt_language,
    prompt_main_path,
    prompt_mode,
    prompt_clustering_strat,
)

from tifo.extractors.metadata import extract_contents

from tifo.pipeline.with_clustering import get_folder_names, with_clustering_pipeline

from tifo.naming.formats import prompt_naming_format
from tifo.pipeline.resources import load_resources
from tifo.pipeline.no_clustering import renaming_pipeline

def run_app():
    welcome_banner()
    language_chosen = prompt_language()
    DIR_PATH = prompt_main_path()
    mode_choice = prompt_mode()
    
    if mode_choice == "rename_only":
        renaming_banner(DIR_PATH)
        
        label, formatter = prompt_naming_format()
        use_date = "YYYY-MM-DD" in label
        
        # loading
        raw_files = extract_contents(root_path=DIR_PATH)
        res = load_resources(needs_embedder=False, needs_llm=True)
        
        renaming_pipeline(formatter=formatter, use_date=use_date, raw_files=raw_files)
        
    elif mode_choice == "clustering":
        strat_choice = prompt_clustering_strat()
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
            res=res
        )
    
    
if __name__ == "__main__":
    run_app()