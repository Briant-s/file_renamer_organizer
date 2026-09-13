from pathlib import Path
from datetime import datetime

from src.extractors.pdf import *
from src.extractors.docx import *
from src.extractors.spreadsheet import *

from rich.progress import track

# Extensions that are always binary — don't attempt read_text() on these
BINARY_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".svg", ".ico", ".heic", ".heif",
    # Video
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    # Audio
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
    # Documents (binary formats)
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    # Executables / compiled
    ".exe", ".dll", ".so", ".bin", ".pyc", ".class",
}

def _read_text_safe(entry: Path) -> tuple[str | None, bool]:
    if entry.suffix.lower() in BINARY_EXTENSIONS:
        return None, True
    try:
        return entry.read_text(encoding="utf-8"), False
    except UnicodeDecodeError:
        # File exists but isn't valid UTF-8 — treat as binary
        return None, True
    except (PermissionError, OSError):
        # Unreadable for OS reasons — still include the file metadata
        return None, False


def extract_contents(root_path: str) -> list[dict]:
    root = Path(root_path)
    files_list = []
    
    for entry in track(root.rglob("*"), description="Reading files..."):
        if entry.is_file():
            info = entry.stat()
            
            file_suffix = entry.suffix.lower()
            
            if file_suffix == ".pdf":
                result = extract_pdf(entry)
                content = result.content
                extra_metadata = result.metadata
                is_binary = True
            elif file_suffix == ".docx":
                result = extract_docx(entry)
                content = result.content
                extra_metadata = result.metadata
                is_binary = True
            elif file_suffix == ".xlsx":
                result = extract_xlsx(entry)
                content = result.content
                extra_metadata = result.metadata
                is_binary = True
            else:
                content, is_binary = _read_text_safe(entry)
                extra_metadata = {}
            
            files_list.append({
                "path": str(entry.resolve()), # Absolute Path
                "parent_dir": str(entry.parent),

                "rel_path": str(entry.relative_to(root)),
                "file_name": entry.name,
                "stem": entry.stem, # Filename without extension
                "file_type": file_suffix or "unknown",

                "size_bytes": info.st_size,
                "created_at": datetime.fromtimestamp(info.st_ctime),
                "content": content,       # None for binary files
                "is_binary": is_binary,
                "metadata": extra_metadata
            })
        
        """
        EXAMPLE
        path: /home/briant_s/Documents/Code/semester_5/Venture/file_renamer/testing_dir1/test1/4.txt
        parent_dir: /home/briant_s/Documents/Code/semester_5/Venture/file_renamer/testing_dir1/test1
        rel_path: test1/4.txt
        file_name: 4.txt
        stem: 4
        file_type: .txt
        size_bytes: 390
        created_at: 2026-09-08 22:11:35.838353
        content: Grocery List
        """
        
    
    return files_list

def show_files(files_list: list[dict]):
    print(f"\n{'FILE':<30} {'TYPE':<8} {'SIZE':>8}   {'CONTENT PREVIEW'}")
    print("-" * 80)
    for f in files_list:
        name = f["file_name"][:28]
        ftype = f["file_type"] or "unknown"
        size = f["size_bytes"]
        size_str = f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"

        if f["content"]:
            # Flatten whitespace and show first 40 chars
            preview = " ".join(f["content"].split())[:40]
            preview = f'"{preview}..."'
        else:
            preview = "[no text content]"

        print(f"{name:<30} {ftype:<8} {size_str:>8}   {preview}")
    print()


def show_files_all(files_list: list[dict]):
    for f in files_list:
        print("--- File Details ---")
        for key, value in f.items():
            print(f"{key}: {value}")
        print()