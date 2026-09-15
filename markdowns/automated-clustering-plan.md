# Automated Clustering — Design Plan

Goal: let the local LLM generate folder categories and cluster files **automatically**,
with no manual folder-name input from the user.

---

## Core Insight

"Generate + cluster automatically" is really **two separate problems**:

1. **Grouping** — which files belong together
2. **Labeling** — what to call each group

The robust design keeps them separate:
- Use **embeddings** for grouping (cheap, deterministic, scalable)
- Use the **LLM only for labeling** (where it's actually good)

### Do NOT ask the LLM to cluster
Dumping all filenames into the LLM and asking it to "group these" is the fragile path:
- Doesn't scale past the context window
- Non-deterministic
- Hallucinates groupings

Robust systems **cluster in embedding space** and use the LLM only to **name** the
resulting clusters.

---

## Proposed Pipeline

### Stage 1 — Extract & embed (already exists)
Reuse `extract_contents` + `model.encode`. Every file becomes a 384-dim vector from its
content (or filename stem fallback). Keep the empty-batch guard already added to
`batch_encode`.

### Stage 2 — Discover clusters (new core)
Run unsupervised clustering on the embeddings. Key requirement: **the number of clusters
is unknown in advance**, so avoid plain k-means (needs `k`).

Options, best-fit first:

- **HDBSCAN** *(recommended for robustness)* — density-based, auto-discovers cluster
  count, and has a built-in **noise/outlier** label (`-1`). Files that don't fit any group
  become "Unsorted" naturally — maps perfectly to the roadmap's Unsorted bucket.
  Tradeoff: extra dependency.
- **Agglomerative clustering with a distance threshold** — no fixed `k` (cut the
  dendrogram at a cosine-distance threshold). Uses sklearn (already transitively present
  via sentence-transformers), fully deterministic, but no native noise bucket (handle
  outliers manually).
- **Tiny-batch fallback** (<~5 files): skip clustering; treat each file individually or as
  one group.

Suggested start: **agglomerative** (no new dependency), offer **HDBSCAN** as an upgrade.

### Stage 3 — Label each cluster with the LLM (repurpose existing pieces)
For each discovered cluster:
1. Pick representative samples — files nearest the cluster **centroid** (most central =
   most representative). Reuse the idea in `build_text_samples`, but sample **per-cluster**.
2. Feed samples to the LLM and ask for a **short folder name**. This is the *inverse* of
   the current `label_expander` (which does label → description). Here it's
   **sample contents → label**. Same `ollama.chat` + `temperature=0` pattern, ideally with
   a Pydantic schema (like `generate_name`) for clean `{folder_name}` output.
3. Deduplicate/merge labels: clusters the LLM names the same get merged.

### Stage 4 — Assign & confidence-gate
Every file gets its cluster's label. Reuse existing confidence logic: files in the noise
bucket (HDBSCAN) or far from any centroid → **"Unsorted"** for user review (Phase 4 UI).

### Stage 5 — Name files & preview (pieces exist)
Run `generate_name` per file, then show the diff-style preview before applying. Fully
automated end-to-end, but with a confirm gate.

---

## Robustness Concerns to Design For

- **Determinism**: embeddings + agglomerative + `temperature=0` LLM = reproducible runs.
  HDBSCAN is also deterministic. Directly helps the "same file, different name across runs"
  edge case.
- **Scale**: clustering in vector space handles thousands of files; the LLM only sees a
  handful of samples per cluster, so token cost is bounded by **cluster count**, not file
  count.
- **Cold start / tiny inputs**: guard for <2 files (can't cluster) and all-identical
  embeddings.
- **Outliers**: never force a file into a bad cluster — surface as Unsorted.
- **Label quality**: constrain the LLM to 1–3 words, validate with Pydantic, strip junk,
  enforce filesystem-safe names.
- **Merging near-duplicate clusters**: after labeling, merge clusters whose centroids are
  very close OR whose labels collide.

---

## How It Reshapes Current Code

- `get_folder_names()` (manual input) becomes **optional** — auto mode skips it entirely.
- `label_expander` (label → description) is **not needed** in auto mode; add a new
  `cluster_labeler` (samples → label) instead.
- `batch_encode` splits: keep the embedding part, replace "assign to user labels" with
  "cluster, then label clusters."
- New pipeline `src/pipeline/auto_clustering.py` alongside `with_clustering.py` /
  `no_clustering.py`, selectable from the `main.py` menu (e.g. "Automatic Folder
  Organizer").

---

## Open Questions (decide before implementing)

1. **New dependency OK?** HDBSCAN = best robustness (native outlier handling). Otherwise
   sklearn agglomerative (no new dep). Which?
2. **Hybrid mode?** Middle ground where the LLM *proposes* categories and the user can
   accept/tweak — or fully hands-off?
3. **Granularity control** — should the user influence how many folders emerge (finer vs.
   coarser grouping), or fully auto?

---

## Suggested Next Step

Lock the design (module layout, function signatures, `cluster_labeler` prompt,
clustering-threshold strategy), then implement `auto_clustering.py` in a follow-up.
