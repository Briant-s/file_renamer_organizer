"""
    Uses paraphrase-multilingual-MiniLM-L12-v2 for the embedder model
    Uses qwen2.5:3b for the main llm prompting

"""

from tifo.classifiers.base import Classifier
from collections import defaultdict
from tifo.classifiers.cluster_namer import name_all_clusters
import umap, hdbscan
import os, re


class AutoClassifier(Classifier):

    def __init__(self, *, embedder, client) -> None:
        self.embedder = embedder
        self.client = client

    @staticmethod
    def _clean_text(text: str, n: int) -> str:
        if not isinstance(text, str):                       # handles None and NaN
            return ""
        text = re.sub(r"&nbsp;|[\u200b\u00a0]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:n]

    @classmethod
    def _build_card(cls, f: dict, n: int) -> str:
        file_name = (f.get("file_name") or f.get("stem") or "unknown").strip()
        ext = os.path.splitext(file_name)[1].lower() or "(none)"
        stripped_contents = cls._clean_text(f.get("content"), n)

        header = f"Filename: {file_name}\nExtension: {ext}"
        if stripped_contents:
            return f"{header}\nContent: {stripped_contents}"
        return f"{header}\nContent: (no extractable text)"

    def classify(self, *, pre_embed: list[dict], on_status=None) -> list[dict]:
        """Cluster files and name each cluster via the LLM.

        ``on_status`` is an optional ``(message: str) -> None`` hook the
        frontend uses to narrate the heavy steps (embedding, clustering,
        LLM naming). It is a no-op when not supplied, so the method stays
        silent as pure core logic and compatible with the base contract.
        """
        embedder = self.embedder

        def status(msg: str) -> None:
            if on_status:
                on_status(msg)

        if not pre_embed:
            print("No files to classify.")
            return []

        # 1. Data Prep
        text_cards = [self._build_card(f, 500) for f in pre_embed]

        # 2. Embed File Contents
        status("Creating embeddings...")
        embedded_contents = embedder.encode(
            text_cards,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        # 3. Dimensionality Reduction using UMAP
        MIN_CLUSTER_SIZE = 4
        n = len(embedded_contents)

        if n < MIN_CLUSTER_SIZE:
            # Too few files to form a cluster; leave them all unsorted.
            for f in pre_embed:
                f["matching_folder"] = None
            return pre_embed

        status("Working on clustering...")
        reducer = umap.UMAP(
            n_components=min(8, n - 2),
            n_neighbors=min(10, n - 1),
            min_dist=0.0,
            metric="cosine",
            random_state=42,
            n_jobs=1,
            compatibility_layout=True,
        )
        reduced = reducer.fit_transform(embedded_contents)

        # 4. HDBSCAN Clustering
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=MIN_CLUSTER_SIZE,
            min_samples=2,
            cluster_selection_method="leaf",
            allow_single_cluster=False,
            metric="euclidean",
            prediction_data=True,
            gen_min_span_tree=True,
        )
        clusterer.fit(reduced)
        labels = clusterer.labels_
        probs = clusterer.probabilities_

        # 5. Group file dicts by cluster_id
        groups: dict[int, list[dict]] = defaultdict(list)
        for f, lab, p in zip(pre_embed, labels, probs):
            f["_prob"] = float(p)
            groups[int(lab)].append(f)

        # 6. LLM Cluster Naming (one call per real cluster; -1 is noise)
        n_clusters = sum(1 for c in groups if c != -1)
        status(f"Naming {n_clusters} folder(s) with the LLM...")
        names = name_all_clusters(groups, self.client)

        for f, lab in zip(pre_embed, labels):
            f["matching_folder"] = names[int(lab)]
            f.pop("_prob", None)
        return pre_embed
