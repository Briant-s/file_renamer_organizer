import pymupdf
from pathlib import Path
from tifo.extractors.models import ExtractedFile

MAX_PAGES = 3

# Currently only extracts text
def extract_pdf(file_path: Path) -> ExtractedFile:
    doc = pymupdf.open(file_path)
    
    pages_text = []
    for page in doc[:MAX_PAGES]:
        pages_text.append(page.get_text())
    full_text = "\n".join(pages_text).strip()
    
    return ExtractedFile(
        content=full_text if full_text else None,
        summary=None,
        metadata=doc.metadata | {"page_count": len(doc)}
    )
    
# if __name__ == "__main__":
#     from pathlib import Path
#     result = extract_pdf(Path("testing_dir1/pdf1.pdf"))
#     print(result)
    
    