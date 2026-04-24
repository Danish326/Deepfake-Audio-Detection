"""
ml/inference/cpu_runner.py

Runs inference on a single model on CPU.

Mirrors the training notebook's evaluation pattern (Cell 15):
    model.eval()
    with torch.no_grad():
        outputs = model(inputs)
        probs = torch.softmax(outputs, dim=1)

DO NOT move tensors to GPU here — CPU-only for v1.
"""
import logging

import torch
import torch.nn.functional as F

logger = logging.getLogger("ml")


def run_inference(model: torch.nn.Module, tensor: torch.Tensor) -> torch.Tensor:
    """
    Run a single model on a single feature tensor.

    Args:
        model:  A ResNet18 model in eval() mode (MelResNet18 or LFCCResNet18).
        tensor: Feature tensor of shape (1, C, H, W) — already batched.

    Returns:
        torch.Tensor of shape (2,) — softmax probabilities [P(real), P(fake)].
    """
    with torch.no_grad():
        outputs = model(tensor)                    # (1, 2) logits
        probs = torch.softmax(outputs, dim=1)      # (1, 2) probabilities

    return probs.squeeze(0)  # → (2,)  [P(real), P(fake)]
