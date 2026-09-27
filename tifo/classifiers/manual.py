from sentence_transformers import util

from tifo.classifiers.base import Classifier
from tifo.embedding.expand_label import label_expander
from tifo.embedding.text_sampler import build_text_samples


def zscore_normalize(matrix):
    mean = matrix.mean()
    std_dev = matrix.std().clamp_min(1e-6)
    return (matrix - mean) / std_dev


class ManualClassifier(Classifier):

    MIN_FILES_FOR_NORMALIZE = 20

    def __init__(self, *, model, folder_labels: list[str]) -> None:
        # Strategy-specific inputs live in the constructor so `classify` stays
        # uniform across all strategies (satisfies the ABC contract).
        self.model = model
        self.folder_labels = folder_labels

    @staticmethod
    def _pick_text(f: dict) -> str:
        # Uses stem for safety falback
        for candidate in (f.get("content"), f.get("stem"), f.get("file_name")):
            if candidate and candidate.strip():
                return candidate.strip()[:1000]
        return "unknown file"

    def classify(self, *, pre_embed: list[dict]) -> list[dict]:
        model = self.model
        folder_labels = self.folder_labels

        # Guard: encoding an empty batch returns a zero-width tensor, so cos_sim
        # crashes with "mat1 and mat2 shapes cannot be multiplied". Bail early.
        if not pre_embed:
            print("No files to classify.")
            return []
        if not folder_labels:
            print("No folder labels provided; nothing to classify against.")
            for f in pre_embed:
                f["matching_folder"] = None
            return pre_embed

        # 0. Get sample context of the working directory
        sample_context = build_text_samples(files=pre_embed)

        # 1. Expand the folder labels and then embed
        folder_map = {
            label: label_expander(label, sample_context) for label in folder_labels
        }
        expanded_labels = list(folder_map.values())
        folder_embeddings = model.encode(expanded_labels, convert_to_tensor=True)

        # 2. Embed file contents (stem fallback handled by _pick_text)
        texts = [self._pick_text(f) for f in pre_embed]
        file_embeddings = model.encode(
            texts, convert_to_tensor=True, batch_size=32, show_progress_bar=True
        )

        # 3. Cosine similarity matrix; normalize for larger batches
        cosine_matrix = util.cos_sim(file_embeddings, folder_embeddings)

        if len(pre_embed) >= self.MIN_FILES_FOR_NORMALIZE:
            matrix = zscore_normalize(cosine_matrix)
            z_threshold, z_gap = 1.0, 0.5
        else:
            matrix = cosine_matrix
            z_threshold, z_gap = 0.15, 0.05

        # 4. Assign each file, gating by threshold + top-2 gap
        results = []
        for i, f in enumerate(pre_embed):
            scores = matrix[i]
            top2 = scores.topk(2)
            top_z, second_z = top2.values[0].item(), top2.values[1].item()
            top_idx = top2.indices[0].item()

            raw_top = cosine_matrix[i][top_idx].item()
            raw_second = cosine_matrix[i][top2.indices[1].item()].item()

            if top_z < z_threshold or (top_z - second_z) < z_gap:
                f["matching_folder"] = None
            else:
                f["matching_folder"] = folder_labels[top_idx]

            f["top_score"] = raw_top
            f["second_score"] = raw_second
            f["top_z"] = top_z
            f["gap_z"] = top_z - second_z
            results.append(f)

        return results
