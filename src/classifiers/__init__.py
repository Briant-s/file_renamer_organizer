"""Folder-classification strategies.

Each strategy is a concrete :class:`Classifier` (see ``base.py``) that assigns
``matching_folder`` to every file. Strategies differ in their constructor args
(manual needs an embedder + labels; file_type needs nothing), so the registry
maps the menu value from ``prompt_clustering_strat`` to the **class** — the
pipeline instantiates the chosen one with its strategy-specific arguments, then
calls ``.classify(pre_embed=...)``.

Only finished strategies are registered. ``auto_organize`` is not yet
implemented and is intentionally omitted until ``AutoClassifier`` exists.
"""

from src.classifiers.base import Classifier
from src.classifiers.manual import ManualClassifier
from src.classifiers.file_type import FileTypeClassifier

# Maps prompt_clustering_strat() values -> classifier class.
CLASSIFIERS: dict[str, type[Classifier]] = {
    "manual": ManualClassifier,
    "file_based": FileTypeClassifier,
}

__all__ = [
    "Classifier",
    "ManualClassifier",
    "FileTypeClassifier",
    "CLASSIFIERS",
]
