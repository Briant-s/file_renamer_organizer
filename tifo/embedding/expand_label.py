from ollama import chat

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
        f"{_SYSTEM_PROMPT}\n\n"
        f'Folder name: "{folder_label}"\n\n'
        f"Here are some real file contents from the directory being organized "
        f"(use these only to understand the vocabulary and context, not to cherry-pick examples):\n"
        f"{sample_text}\n\n"
        f'Write a general one-sentence description of the broad category of content '
        f'that belongs in a folder called "{folder_label}". '
        f"Cover the range of relevant topics, not just what appears in the samples. "
        f"Respond with only the description."
    )

    response = chat(
        model="llama3.2:3b",
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        options={"temperature": 0}
    )
    return response.message.content.strip()