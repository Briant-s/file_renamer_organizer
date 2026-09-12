from pathlib import Path
import shutil

def rename(old: str, new:str, testing_dir: str = "copy_testing"):
    # Turn into Path objects
    source = Path(old)
    dest_folder = Path(testing_dir)
    
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    extension = source.suffix if not Path(new).suffix else ""
    target = dest_folder / f"{new}{extension}"
    
    if target.exists():
        print(f"ERROR! File named '{target.name} already exists in '{dest_folder}'")
    
    
    try:
        shutil.copy2(source, target)
        print(f"Successfully copied & renamed '{source.name}' -> '{new}'")
    except FileNotFoundError:
            print(f"ERROR! Source file doesn't exists")
    except FileExistsError:
            print(f"ERROR! A file named '{new}' already exists")
    except PermissionError:
            print("ERROR! Insuficcient permisions to rename this file")
    except OSError as e:
            print(f"Operating System Error Occured: {e}")