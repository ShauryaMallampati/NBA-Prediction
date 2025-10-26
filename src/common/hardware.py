from __future__ import annotations
import torch

def pick_device(preferred: str = "mps") -> str:
    try:
        if preferred == "mps" and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"
