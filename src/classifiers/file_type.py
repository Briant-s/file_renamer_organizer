from src.classifiers.base import Classifier

TEMP_EXT_MAP: dict[str, str] = {
    # Documents
    ".pdf": "Documents",
    ".docx": "Documents",
    ".doc": "Documents",
    ".txt": "Documents",
    ".md": "Documents",
    ".rtf": "Documents",
    ".odt": "Documents",
    # Spreadsheets
    ".xlsx": "Spreadsheets",
    ".xls": "Spreadsheets",
    ".csv": "Spreadsheets",
    # Presentations
    ".pptx": "Presentations",
    ".ppt": "Presentations",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".webp": "Images",
    ".heic": "Images",
    # Video
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".mov": "Videos",
    ".avi": "Videos",
    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".m4a": "Audio",
    # Archives
    ".zip": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".rar": "Archives",
    # Code
    ".py": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".java": "Code",
    ".c": "Code",
    ".cpp": "Code",
    ".rs": "Code",
    ".go": "Code",
}

class FileTypeClassifier(Classifier):
    def __init__(self, *, ext_map: dict[str, str] | None = None) -> None:
        self.ext_map = ext_map or TEMP_EXT_MAP
        
    def classify(self, *, pre_embed: list[dict]) -> list[dict]:
        for f in pre_embed:
            suffix = f.get("file_type", "").lower()
            f["matching_folder"] = self.ext_map.get(suffix)
        return pre_embed

if __name__ == "__main__":
    fake = [
        {"file_name": "invoice.pdf", "file_type": ".pdf", "content": None},
        {"file_name": "photo.JPG",   "file_type": ".jpg", "content": None},
        {"file_name": "clip.mp4",    "file_type": ".mp4", "content": None},
        {"file_name": "weird.xyz",   "file_type": ".xyz", "content": None},  # -> None
    ]
    results = FileTypeClassifier().classify(pre_embed=fake)
    for f in results:
        print(f["file_name"], "->", f["matching_folder"])
    