import docx2txt
from pathlib import Path
from tifo.extractors.models import ExtractedFile

def extract_docx(file_path: Path) -> ExtractedFile:
    extracted_text = docx2txt.process(str(file_path))
    
    return ExtractedFile(
        content=extracted_text.strip() if extracted_text.strip() else None,
        summary=None,
        metadata={}
    )

# if __name__ == "__main__":
#     from pathlib import Path
#     text = extract_docx(Path("testing_dir1/sample.docx"))
#     print(text)   
