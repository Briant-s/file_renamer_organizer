from sentence_transformers import SentenceTransformer, util
from src.ai.expand_label import *
from src.ai.text_sampler import *

def get_folder_names() -> list[str]:
    folder_lists = []
    
    while True:
        user_input = input("Enter folder name ('quit' to exit) >> ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        folder_lists.append(user_input)
    
    print(f"Your final list: {folder_lists}")
    return folder_lists

def embedding_prep(raw_data_list: list[dict]) -> list[dict]:
    pre_embed = [
        {
            "file_name": item["file_name"],
            "stem": item.get("stem", item["file_name"]),  # kept for binary fallback
            "content": item["content"],
        }
        for item in raw_data_list
    ]
    
    return pre_embed

def zscore_normalize(matrix):
    mean = matrix.mean()
    std_dev = matrix.std().clamp_min(1e-6)
    return (matrix - mean) / std_dev

def batch_encode(model: SentenceTransformer, folder_labels: list[str], pre_embed: list[dict]):
    # 0. Get sample context of the working directory
    sample_context = build_text_samples(files=pre_embed)
    
    # 1. Expand the folder labels and then embed
    folder_map = {label: label_expander(label, sample_context) for label in folder_labels}
    print(folder_map)
    expanded_labels = list(folder_map.values())
    folder_embeddings = model.encode(expanded_labels, convert_to_tensor=True)
    
    # 2. Embed file contents
    # For binary/unreadable files, fall back to the filename stem as the semantic signal
    # (e.g. "vacation_beach.jpg" -> "vacation_beach", "invoice_2024.pdf" -> "invoice_2024")
    texts = [
        (f["content"][:1000] if f.get("content") else f.get("stem", f["file_name"]))
        for f in pre_embed
    ]
    file_embeddings = model.encode(texts, convert_to_tensor=True, batch_size=32, show_progress_bar=True)
     
    # 3. Create cosine similarity matrix and normalize if needed
    cosine_matrix = util.cos_sim(file_embeddings, folder_embeddings)
    
    min_files_for_normalize = 20
    if len(pre_embed) >= min_files_for_normalize:
        matrix = zscore_normalize(cosine_matrix)
        z_treshold, z_gap = 1.0, 0.5
    else:
        matrix = cosine_matrix
        z_treshold, z_gap = 0.15, 0.05
    
    results = []
    for i, f in enumerate(pre_embed):
        z_scores = matrix[i]
        top2 = z_scores.topk(2)
        top_z, second_z = top2.values[0].item(), top2.values[1].item()
        top_idx = top2.indices[0].item()
        
        raw_top = cosine_matrix[i][top_idx].item()
        raw_second = cosine_matrix[i][top2.indices[1].item()].item()


        if top_z < z_treshold or (top_z - second_z) < z_gap:
            f["matching_folder"] = None
        else:
            f["matching_folder"] = folder_labels[top_idx]

        f["top_score"] = raw_top
        f["second_score"] = raw_second
        f["top_z"] = top_z
        f["gap_z"] = top_z - second_z
        results.append(f)
        
    
    
    for f in results:
        print(f"{f["file_name"]}: {f["matching_folder"]} -> {f["top_score"]} | {f["second_score"]}")
    
def clustering_flow(model: SentenceTransformer, raw_data: list[dict]) -> None:
    # 1. Get folder labels from users
    folder_labels = get_folder_names()
    
    # 2. Extract and reformat file metadata 
    pre_embed = embedding_prep(raw_data)
    
    batch_encode(
        model=model,
        folder_labels=folder_labels,
        pre_embed=pre_embed
    )
    
    