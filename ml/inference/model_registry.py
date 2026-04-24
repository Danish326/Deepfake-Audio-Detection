"""
ml/inference/model_registry.py

Loads and holds all 8 ResNet18 models in memory.

Called once at application startup via FastAPI's lifespan hook.
All subsequent requests share the same in-memory models — never reload per request.

Model key format: (batch, feature)
    batch   ∈ {"data3", "data5", "data6", "data8"}
    feature ∈ {"mel", "lfcc"}

Checkpoint format (from training notebook, Cell 15 test() function):
    checkpoint = torch.load(path, map_location="cpu")
    state_dict = checkpoint['model_state_dict']
    model.load_state_dict(state_dict)
"""
import logging
import os
from typing import Dict, Optional, Tuple

import torch

from ml.models.mel_resnet18 import MelResNet18
from ml.models.lfcc_resnet18 import LFCCResNet18
from ml.utils.constants import MODEL_BATCHES, MODEL_FEATURES, get_model_weight_path
from ml.utils.exceptions import ModelLoadError, ModelNotLoadedError

logger = logging.getLogger("ml")

# Global in-memory model store
# Key: (batch, feature)  e.g. ("data3", "mel")
# Value: nn.Module in eval() mode
_REGISTRY: Dict[Tuple[str, str], torch.nn.Module] = {}

# Track load status per model for health endpoint
_LOAD_STATUS: Dict[str, bool] = {}


def _build_model(feature: str) -> torch.nn.Module:
    """Instantiate the correct architecture class for a given feature type."""
    if feature == "mel":
        return MelResNet18(num_classes=2)
    elif feature == "lfcc":
        return LFCCResNet18(num_classes=2)
    else:
        raise ValueError(f"Unknown feature type: {feature}")


def load_all_models(weights_root: str = "ml/weights") -> None:
    """
    Load all 8 models from disk into _REGISTRY.

    Uses the exact loading pattern from the training notebook (Cell 15):
        checkpoint = torch.load(path, map_location="cpu")
        state_dict = checkpoint['model_state_dict']
        model.load_state_dict(state_dict)
        model.eval()

    Args:
        weights_root: Root directory containing batch subfolders.

    Logs:
        One INFO line per model loaded successfully.
        One ERROR line per model that fails, without crashing startup.
    """
    for batch in MODEL_BATCHES:
        for feature in MODEL_FEATURES:
            key = (batch, feature)
            status_key = f"{feature}_{batch}"
            path = get_model_weight_path(feature, batch, weights_root)

            if not os.path.exists(path):
                logger.error(
                    "Model weight not found: %s — skipping (key=%s)",
                    path, key
                )
                _LOAD_STATUS[status_key] = False
                continue

            try:
                model = _build_model(feature)
                checkpoint = torch.load(path, map_location=torch.device("cpu"))
                state_dict = checkpoint["model_state_dict"]
                model.load_state_dict(state_dict)
                model.eval()

                _REGISTRY[key] = model
                _LOAD_STATUS[status_key] = True
                logger.info("Loaded model: %s/%s from %s", batch, feature, path)

            except Exception as exc:
                logger.error(
                    "Failed to load model %s/%s from %s: %s",
                    batch, feature, path, exc
                )
                _LOAD_STATUS[status_key] = False

    loaded = sum(_LOAD_STATUS.values())
    total = len(MODEL_BATCHES) * len(MODEL_FEATURES)
    logger.info("Model registry: %d/%d models loaded.", loaded, total)


def get_model(batch: str, feature: str) -> torch.nn.Module:
    """
    Retrieve a model from the registry.

    Raises:
        ModelNotLoadedError: If the requested model was not loaded at startup.
    """
    key = (batch, feature)
    model = _REGISTRY.get(key)
    if model is None:
        raise ModelNotLoadedError(
            f"Model ({batch}, {feature}) is not loaded. "
            "Check startup logs for weight file errors."
        )
    return model


def get_load_status() -> Dict[str, bool]:
    """Return a dict of {model_key: bool} for the health endpoint."""
    return dict(_LOAD_STATUS)


def all_models_loaded() -> bool:
    """True only when all 8 models loaded successfully."""
    return (
        len(_LOAD_STATUS) == len(MODEL_BATCHES) * len(MODEL_FEATURES)
        and all(_LOAD_STATUS.values())
    )
