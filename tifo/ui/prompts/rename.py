import questionary

from tifo.naming.formats import prompt_naming_format as _prompt_naming_format
from tifo.ui.display.feedback import select_reaction

def prompt_naming_format():
    # Delegate to the canonical implementation (builds choices + returns the
    # formatter), then add this layer's select_reaction feedback.
    chosen, formatter = _prompt_naming_format()
    select_reaction(chosen)
    return chosen, formatter

def prompt_rename_option(*, is_folder: bool):
    text = "Folder Options" if is_folder else "Renames"
    
    rename_option = questionary.select(
        f"Apply Current {text}?",
        choices=[
            questionary.Choice(title="Accept All", value="accept"),
            # questionary.Choice(title="Individual Edit", value="manual"),
            questionary.Choice(title="Cancel", value="cancel"),
        ],
        default="accept"
    ).ask()
    select_reaction(rename_option)
    return rename_option


def prompt_rename_or_move() -> bool:
    """After folder confirmation, ask whether to rename files too.

    Returns True for rename+move (AI generates names, slower), False for
    move-only (keep original names, fast — no LLM calls).
    """
    choice = questionary.select(
        "How should files be placed into folders?",
        choices=[
            questionary.Choice(title="Move only (keep names, fast)", value="move"),
            questionary.Choice(title="Rename + move (AI names, slower)", value="rename"),
        ],
        default="move",
    ).ask()
    select_reaction(choice)
    return choice == "rename"