from __future__ import annotations

import json, os, re

from tifo.config import LLM_MODEL, PROPERTIES


def clean_text(text, n: int) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"&nbsp;|[\u200b\u00a0]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n]


def sanitize_name(raw: str, max_words: int = 4) -> str:
    s = re.sub(r"[^\w\s-]", " ", raw, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", " ", s).strip()
    words = s.split()[:max_words]
    return " ".join(w.capitalize() if w.islower() else w for w in words) or "Unnamed"


def pick_reps(members: list[dict], n: int = 6) -> list[dict]:
    ordered = sorted(members, key=lambda f: f.get("_prob", 0.0), reverse=True)
    if len(ordered) <= n:
        return ordered
    return ordered[: n - 1] + ordered[-1:]


FREE_NAME_SYSTEM = (
    "You name groups of files for a folder organizer. The files were grouped automatically "
    "because their contents are similar.\n"
    "Give ONE short folder name (2-4 words) for the SHARED TOPIC or SUBJECT of the group.\n"
    "Rules:\n"
    "- Write the name in English, even if the files are in Indonesian.\n"
    "- Base it on words that actually appear in the filenames or content. Do not invent a subject.\n"
    "- Do not use generic names such as Documents, Files, Misc, General or Folder.\n"
    "- If the files share no clear topic, answer: Mixed Files"
)
 
FREE_NAME_SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
}


def name_cluster_free(members: list[dict], client, *, model: str = LLM_MODEL,
                    n_files: int = 6, snippet_chars: int = 250) -> str:
    lines = []
    for f in pick_reps(members, n_files):
        fname = f.get("file_name", "unknown")         
        snippet = clean_text(f.get("content"), snippet_chars)
        lines.append(f"- {fname}" + (f" | {snippet}" if snippet else ""))

    resp = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": FREE_NAME_SYSTEM},
            {"role": "user", "content": "Files:\n" + "\n".join(lines) + "\n\nFoldername:"},
        ],
        format=FREE_NAME_SCHEMA,
        keep_alive="10m",
        options=PROPERTIES
    )
    return sanitize_name(json.loads(resp["message"]["content"])["name"])


def name_all_clusters(groups: dict[int, list[dict]], client, **kw) -> dict[int, str | None]:
    """cluster id -> folder name. Noise (-1) -> None. Duplicate names get a suffix."""
    names: dict[int, str | None] = {}
    used: dict[str, int] = {}
    for cluster_id, members in groups.items():
        if cluster_id == -1:
            names[cluster_id] = None
            continue
        name = name_cluster_free(members, client, **kw)
        used[name] = used.get(name, 0) + 1
        names[cluster_id] = name if used[name] == 1 else f"{name} {used[name]}"
    return names