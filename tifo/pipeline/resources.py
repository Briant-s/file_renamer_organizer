from dataclasses import dataclass
from typing import TYPE_CHECKING

from tifo.embedding.model import load_embedder_model
from tifo.ui.display.feedback import loading

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@dataclass
class Resources:
    embedder: "SentenceTransformer | None" = None
    llm_ready: bool = False

def warm_llm(model: str) -> bool:
    try: 
        from ollama import chat
        chat(model=model, 
             messages=[{
                 "role": "user",
                 "content": "this prompt is to warmup the llm call, just reply with 0 or 1 accordingly"
             }],
            options={"num_predict": 1}     
        )
        return True
    except Exception as e:
        print(f"[LLM] not ready: {type(e).__name__}: {e}")
        return False
    
    
def run_test(device: str = "cpu") -> None:
    """Measure where embedder load time goes: imports vs weights vs first encode."""
    import time

    t = time.perf_counter()
    import torch  # noqa: F401
    print(f"torch import:     {time.perf_counter() - t:.2f}s")

    t = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    print(f"ST import:        {time.perf_counter() - t:.2f}s")

    t = time.perf_counter()
    m = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    print(f"model load ({device}): {time.perf_counter() - t:.2f}s")

    t = time.perf_counter()
    m.encode(["health check"])
    print(f"first encode:     {time.perf_counter() - t:.2f}s")


def load_resources(*, needs_embedder: bool, needs_llm: bool, llm_model: str = "llama3.2:3b") -> None:
    res = Resources()
    
    if needs_embedder:
        # load_embedder_model owns its own detailed status spinner,
        # so we must NOT wrap it in loading(...) — nested console.status conflicts.
        res.embedder = load_embedder_model()
    
    if needs_llm:
        with loading("Warming up LLM..."):
            res.llm_ready = warm_llm(llm_model) 
            
    return res

if __name__ == "__main__":
    # res = load_resources(needs_embedder=False, needs_llm=True)
    res1 = load_resources(needs_embedder=True, needs_llm=True)
    # run_test()
    print(res1)