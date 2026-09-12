import torch
from sentence_transformers import SentenceTransformer

_model = None

def get_optimal_device() -> str:
    if torch.cuda.is_available():
        print("Testing CUDA if possible!")
        try:
            a = torch.zeros(2, 2, device="cuda")
            _ = a @ a 
            torch.cuda.synchronize()
            print("CUDA successfully works!")
            return "cuda"
        except Exception:
            print("CUDA doesnt work, defaulting to CPU")
            return "cpu"
    
    if torch.backends.mps.is_available():
        return "mps"

    return "cpu"

def load_embedder_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading embedder model")
        device = get_optimal_device()
        _model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    return _model