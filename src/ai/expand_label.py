from ollama import chat

model_prompt = """
Expand the given folder name with a solid one-sentence description of what 
file content would belong in it. Respond only with the description and no preamble
Folder Name: 
"""


def label_expander(folder_label: str, sample_context: list[str]) -> str:
    prompt = (
        f"{model_prompt}\n\n"
        f'Folder name: "{folder_label}"\n\n'
        f"Here are some real file contents from the directory being organized:\n"
        f"{sample_context}\n\n"
        f'Write a short description of what belongs in a folder called "{folder_label}", '
        f"reusing the vocabulary and subjects from the samples above where relevant. "
        f"Respond with only the description."
    )
    
    response = chat(
        model="llama3.2:1b",
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        options={"temperature": 0}
    )
    return response.message.content.strip()