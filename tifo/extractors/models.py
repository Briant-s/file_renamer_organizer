from pydantic import BaseModel
from typing import Any

class ExtractedFile(BaseModel):
    content: str | None
    summary: str | None
    metadata: dict[str, Any] = {}
    
