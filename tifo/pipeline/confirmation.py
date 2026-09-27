from collections import defaultdict
from rich.console import Console
from rich.tree import Tree


def _group_by_folder(matching_results: list[dict]) -> dict[str, list[str]]:
    folder_buckets: dict[str, list[str]] = defaultdict(list)
    for f in matching_results:
        folder = f.get("matching_folder") or "Unsorted"
        folder_buckets[folder].append(f["file_name"])
    
    return folder_buckets




def preview_folders(*, matching_results: list[dict]) -> None:
    console = Console()
    folder_buckets = _group_by_folder(matching_results)
    
    def _order_format(name: str):
        return (name =="Unsorted", name.lower())
        
    root = Tree("[bold]Folder Organization Preview[/bold]")
    
    for folder in sorted(folder_buckets, key=_order_format):
        style = "yellow" if folder == "Unsorted" else "green"
        branch = root.add(f"[{style}]{folder}[/{style}]  ({len(folder_buckets[folder])})")
        for file_name in sorted(folder_buckets[folder]):
            branch.add(f"{file_name}")
            
    console.print(root)
    
if __name__ == "__main__":
    fake_results = [
          {"file_name": "invoice_2024.pdf", "matching_folder": "Documents"},
          {"file_name": "report.docx",      "matching_folder": "Documents"},
          {"file_name": "notes.txt",        "matching_folder": "Documents"},
          {"file_name": "beach.jpg",        "matching_folder": "Images"},
          {"file_name": "logo.png",         "matching_folder": "Images"},
          {"file_name": "app_idea_notes.txt", "matching_folder": None},   # -> Unsorted
      ]
    preview_folders(matching_results=fake_results)
  