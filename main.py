import warnings
import os
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from datetime import datetime

from tifo.extractors.metadata import *
from tifo.naming.generator import *
from tifo.renaming.renamer import *
from tifo.clustering_flow import *
from tifo.embedding.model import *



from tifo.pipeline.no_clustering import no_clustering_pipeline
from tifo.pipeline.with_clustering import with_clustering_pipeline

import questionary
from rich.console import Console


def main() -> None:
    # rich ui
    console = Console()
    
    # Ask for working dir
    DIR_PATH = questionary.path(
        "Enter folder path to organize (tab for autocomplete) >> "
    ).ask()
    
    # Loading models
    with console.status("Loading embedder model..."):
        model = load_embedder_model()
    
    # Prerequisites
    current_files = extract_contents(DIR_PATH)
    
    # Menu
    choice = questionary.select(
        "Menu List",
        choices=[
            "Renaming Only",
            "With Folder Organizer"
        ]
    ).ask()
    
    if choice == "Renaming Only":
        no_clustering_pipeline(DIR_PATH)
    elif choice == "With Folder Organizer":
        with_clustering_pipeline(DIR_PATH)
        
        
    
    # files = read_files(DIR_PATH) # Extract metadata for all files
    # show_files_all(files) # prints out all files
    # for f in files:
    #     new_name = generate_name(f["content"], f["file_name"])
    #     rename(f["path"], new_name)
    

if __name__ == "__main__":
    main()