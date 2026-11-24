from ollama import chat

from tifo.config import LLM_MODEL

_SYSTEM_PROMPT = """
You are helping classify files into folders. Given a folder name, write a single sentence
describing the general *category* of content that belongs there.
Be broad and inclusive — cover the range of topics that naturally fall under this folder,
not just examples from the files shown.
Respond with only the description, no preamble.
"""


def label_expander(folder_label: str, sample_context: list[str]) -> str:
    sample_text = "\n---\n".join(sample_context) if sample_context else "(no samples available)"

    prompt = (
        f"You are helping to sort documents into folders. Respond with only the description, no preamble."
        f"All folders: {folder_label}"
        f"List 10-15 short keywords or phrases (English and Indonesian) describing the TYPE and FORMAT of documents that belong in the folders list, and what makes them different from the other folders."
        f"Describe document formats, typical headings, and wording, NOT academic subjects."
        f"Output a comma-separated list only"
    )

    response = chat(
        model=LLM_MODEL,
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        options={"temperature": 0}
    )
    return response.message.content.strip()

def format_label(folder_label: str) -> str:
    return f"A document in the folder {folder_label}"