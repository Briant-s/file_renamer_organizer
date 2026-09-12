from pydantic import BaseModel
from ollama import chat

class FileMetaData(BaseModel):
    topic: str

def generate_name(extracted_text: str, original_file: str):
    print("Original File Name: ", original_file)
    print("Analyzing Text with AI...")
    
    prompt = chat(
        model="llama3.2:1b",
        messages=[{
            "role": "user",
            "content": f"extract a 2 word topic from this text\n\n{extracted_text}",
        }],
        format= FileMetaData.model_json_schema(),
        options={"temperature": 0}
    )
    
    ai_response = FileMetaData.model_validate_json(prompt.message.content)
    
    new_name = f'{ai_response.topic}.txt'
    
    print("=== RESULTS ===")
    print(original_file, " ---->", new_name)

    return new_name

    