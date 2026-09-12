from pathlib import Path
from datetime import datetime


def extract_contents(path: str) -> list[dict]:
    root = Path(path)
    files_list = []
    
    for entry in root.rglob("*"):
        if entry.is_file():
            info = entry.stat()
            files_list.append({
                "path": str(entry.resolve()), # Absolute Path
                "parent_dir": str(entry.parent), 
                
                
                "rel_path": str(entry.relative_to(root)),
                "file_name": entry.name,
                "stem": entry.stem, # Filename without extension
                "file_type": entry.suffix or "unkown",
                
                "size_bytes": info.st_size,
                "created_at": datetime.fromtimestamp(info.st_ctime),
                "content": entry.read_text()
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
    for f in files_list:
        print(f'{f["path"]} - {f["size_bytes"]} bytes - {f["created_at"]}')
        
        
def show_files_all(files_list: list[dict]):
    for f in files_list:
        print("--- File Details ---")
        for key, value in f.items():
            print(f"{key}: {value}")
        print() 