from sentence_transformers import util

from tifo.classifiers.base import Classifier
from tifo.embedding.expand_label import label_expander, format_label
from tifo.embedding.text_sampler import build_text_samples
import pandas as pd
import torch


def zscore_normalize(matrix):
    mean = matrix.mean()
    std_dev = matrix.std().clamp_min(1e-6)
    return (matrix - mean) / std_dev


class ManualClassifier(Classifier):

    def __init__(self, *, model, folder_labels: list[str]) -> None:
        # Strategy-specific inputs live in the constructor so `classify` stays
        # uniform across all strategies (satisfies the ABC contract).
        self.model = model
        self.folder_labels = folder_labels

    @staticmethod
    # Creates filename + 500 content preview
    def _build_text(f: dict) -> str:
        file_name = (f.get("file_name") or f.get("stem") or "unknown").strip()
        content_preview = (f.get("content") or "").strip()[:500]
        
        return f"Filename:{file_name}\nContent:{content_preview}" if content_preview else f"Filename:{file_name}"

    def classify(self, *, pre_embed: list[dict]) -> list[dict]:
        model = self.model
        folder_labels = self.folder_labels

        if not pre_embed:
            print("No files to classify.")
            return []
        if not folder_labels:
            print("No folder labels provided; nothing to classify against.")
            for f in pre_embed:
                f["matching_folder"] = None
            return pre_embed


        # 1. Expand the folder labels and then embed
        folder_map = {
            label: format_label(label) for label in folder_labels 
        }
        expanded_labels = list(folder_map.values())
        # print(expanded_labels)
        folder_embeddings = model.encode(expanded_labels, convert_to_tensor=True)

        # 2. Embed file contents (stem fallback handled by _pick_text)
        texts = [self._build_text(f) for f in pre_embed]
        # print(texts)

        file_embeddings = model.encode(
            texts, convert_to_tensor=True, batch_size=32, show_progress_bar=True
        )

        # 3. Cosine similarity matrixs
        cosine_matrix = util.cos_sim(file_embeddings, folder_embeddings)
        
        
        # 4.
        results = []
        MIN_SIM = 0.0
        centered = cosine_matrix - cosine_matrix.mean(dim=0, keepdim=True)
        best_idx = centered.argmax(dim=1)                      # winner, from centered

        rows = torch.arange(cosine_matrix.size(0), device=cosine_matrix.device)
        best_scores = cosine_matrix[rows, best_idx]            # score, from raw
        
        for i, f in enumerate(pre_embed):
            score = best_scores[i].item()
            folder = folder_labels[best_idx[i].item()]
            
            f["best_folder"] = folder
            f["best_score"] = score
            f["matching_folder"] = folder if score >= MIN_SIM else None
            results.append(f)
        
        

        return results
