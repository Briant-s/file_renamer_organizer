from src.extractors.metadata import extract_contents

def with_clustering_pipeline(dir_path: str):
    # 1. Read & extract files first
    raw_files = extract_contents(dir_path)
    
    # 2. 
    