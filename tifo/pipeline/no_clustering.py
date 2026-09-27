from tifo.naming.formats import *
from tifo.renaming.renamer import *
from tifo.naming.generator import *
from tifo.ui.display.preview import *
from rich.progress import track

from tifo.ui.prompts.rename import prompt_rename_option

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


def renaming_pipeline(*, formatter: callable, use_date: bool, raw_files: list[dict]):
    # 3. Save for later comparison
    old_names = get_old_names(raw_files)
    
    # 4. Generate new names using local llm
    new_names = get_new_names(raw_files, formatter, use_date)
    
    # 5. Show the user the old vs new name comparison
    compare_results(old_names, new_names)
    
    # 6. Ask for confirmation from the user
    user_actions = prompt_rename_option(is_folder=False)
    
    if user_actions == "cancel":
        print("No changes were made.")
        return
    elif user_actions == "accept":
        renamed, skipped, failed = rename_flow(raw_files, new_names)
        show_rename_results(renamed, skipped, failed)
        return
    elif user_actions == "manual":
        pass
    
        
    
    
    