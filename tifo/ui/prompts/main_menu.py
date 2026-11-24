import questionary
from rich.console import Console

from tifo.ui.display.feedback import select_reaction

console = Console()

LANGUAGES = ["English", "Indonesian"]


def prompt_language():
    language = questionary.select(
        "Select Language",
        choices=[
            questionary.Choice(title="English (Default)", value="eng"),
            # questionary.Choice(title="Indonesian (NOT SET)", value="ind")    
        ],
        default="eng",
        
    ).ask()
    select_reaction(language)
    return "eng"

def prompt_main_path():
    DIR_PATH = questionary.path(
        "Enter folder path to organize (tab for autocomplete)",
        only_directories=True
    ).ask()
    select_reaction(DIR_PATH)
    return DIR_PATH

def prompt_mode():
    mode_choice = questionary.select(
        "Select pipeline",
        choices=[
            questionary.Choice(title="Rename Files Only", value="rename_only"),
            questionary.Choice(title="Rename + Folder Organization", value="clustering")
        ]
    ).ask()
    select_reaction(mode_choice)
    return mode_choice

def prompt_describe_or_reformat() -> bool:
    """Ask whether to generate new names from content or just reformat existing ones.

    Returns True to describe (AI reads content, slower), False to reformat only
    (restyle the existing filenames instantly, no LLM).
    """
    choice = questionary.select(
        "How should files be named?",
        choices=[
            questionary.Choice(
                title="Reformat existing names (instant, no AI)", value="reformat"
            ),
            questionary.Choice(
                title="Describe from content (AI reads each file, slower)",
                value="describe",
            ),
        ],
        default="reformat",
    ).ask()
    select_reaction(choice)
    return choice == "describe"


def prompt_clustering_strat():
    strat_choice = questionary.select(
        "Select Folder Strategy",
        choices= [ 
            questionary.Choice(title="Manually Write Folder Names", value="manual"),
            questionary.Choice(title="Organize by File Type", value="file_based"),
            questionary.Choice(title="Auto Organize", value="auto_organize")
        ]
    ).ask()
    select_reaction(strat_choice)
    return strat_choice
    