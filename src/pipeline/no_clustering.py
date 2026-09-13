from src.utils.naming_formats import *
from src.ai.generator import *
from src.utils.comparison import *
from rich.progress import track
from src.extractors.metadata import extract_contents

def get_old_names(raw_files: list[dict]) -> list[str]:
    old_names = []
    for f in raw_files:
        old_names.append(f["file_name"])
    
    return old_names

def get_new_names(raw_files: list[dict], formatter: callable, use_date: bool) -> list[str]:
    new_names = []
    
    for f in track(raw_files, description="Generating file names..."):
        new_name = generate_name(f["content"], f["file_name"], formatter, f["created_at"], use_date)
        new_names.append(new_name)
    
    return new_names

def no_clustering_pipeline(dir_path: str):
    # 1. Read & extract files
    raw_files = extract_contents(dir_path)
    
    # 2. Prompt for naming formats
    label, formatter = prompt_naming_format()
    use_date = "YYYY-MM-DD" in label
    
    # 3. Save for later comparison
    old_names = get_old_names(raw_files)
    
    # 4. Generate new names using local llm
    new_names = get_new_names(raw_files, formatter, use_date)
    
    # 5. Show the user the old vs new name comparison
    compare_results(old_names, new_names)
    
    # 6. Ask for confirmation from the user
    
    
    
    