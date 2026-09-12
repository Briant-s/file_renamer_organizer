import random

def build_text_samples(files: list[dict], max_samples: int = 8, sample_len: int = 500) -> list[str]:
    candidates = [f for f in files if f.get("content")]
    if not candidates:
        return []

    chosen_samples = random.sample(candidates, k=min(max_samples, len(candidates)))
    return [f["content"] for f in chosen_samples]

