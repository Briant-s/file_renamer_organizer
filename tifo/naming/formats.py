import re
import questionary
from datetime import datetime

from tifo.common.util import require

NAMING_FORMATS = {
    "Title Case":            lambda s: s.title(),
    "snake_case":            lambda s: re.sub(r"\s+", "_", s.strip().lower()),
    "kebab-case":            lambda s: re.sub(r"\s+", "-", s.strip().lower()),
    "lowercase":             lambda s: s.strip().lower(),
    "UPPERCASE":             lambda s: s.strip().upper(),
    "YYYY-MM-DD Title Case": lambda s: s.title(),
    "YYYY-MM-DD snake_case": lambda s: f"{re.sub(r'\\s+', '_', s.strip().lower())}",
}

_EXAMPLE = "quarterly budget report"


def prompt_naming_format() -> tuple[str, callable]:
    choices = [
        questionary.Choice(
            title=f"{label:<14} → '{NAMING_FORMATS[label](_EXAMPLE)}'",
            value=label
        )
        for label in NAMING_FORMATS
    ]

    chosen_label = require(questionary.select(
        "Choose a naming format:",
        choices=choices,
        default=choices[0],  # Title Case
    ).ask())
    

    return chosen_label, NAMING_FORMATS[chosen_label]


def apply_naming_format(raw_name: str, formatter: callable) -> str:
    cleaned = " ".join(raw_name.strip().split())
    return formatter(cleaned)


# if __name__ == "__main__":
#     chosen_format, formatter = prompt_naming_format()
#     print(f"User's Chosen Format: {chosen_format}")
#     print(f"Formatter Used: {formatter}")