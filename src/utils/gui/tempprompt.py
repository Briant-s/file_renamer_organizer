import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.utils.gui.reactions import *
from src.utils.gui.banners import *

from pathlib import Path


from src.utils.gui.prompts.main_menu import *

console = Console()

LANGUAGES = ["English", "Indonesian"]




if __name__ == "__main__":
    welcome_banner()
    language_chosen = prompt_language()
    DIR_PATH = prompt_main_path()
    mode_choice = prompt_mode()
    
    if mode_choice == "rename_only":
        renaming_banner(DIR_PATH)
    elif mode_choice == "clustering":
        strat_choice = prompt_clustering_strat()
        clustering_banner(strat_choice, DIR_PATH)