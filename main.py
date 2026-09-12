from pathlib import Path
from datetime import datetime

from src.extractors.metadata import *
from src.ai.generator import *
from src.utils.renamer import *
from src.clustering_flow import *
from src.ai.model import *

from simple_term_menu import TerminalMenu


DIR_PATH = '/home/briant_s/Documents/Code/semester_5/Venture/file_renamer/testing_dir1'


def main() -> None:
    # Loading models
    model = load_embedder_model()
    
    # Menu
    options = ["[0] Renamer", "[1] Folder Clustering"]
    main_menu = TerminalMenu(options)
    main_index = main_menu.show()
    print(f"You've Selected {main_index}!")
    
    # Prerequisites
    current_files = extract_contents(DIR_PATH)
    
    
    if main_index == 1:
        clustering_flow(model=model, raw_data=current_files)
        
        
    
    # files = read_files(DIR_PATH) # Extract metadata for all files
    # show_files_all(files) # prints out all files
    # for f in files:
    #     new_name = generate_name(f["content"], f["file_name"])
    #     rename(f["path"], new_name)
    

if __name__ == "__main__":

    main()