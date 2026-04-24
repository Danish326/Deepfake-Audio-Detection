"""
ml/utils/constants.py

Frozen configuration constants for the ML pipeline.

CRITICAL: Every value here that affects audio processing or model input
MUST match the exact values used during training. Any drift between these
values and the training pipeline will silently degrade model accuracy.

All numeric values are loaded from environment variables (with training-time
defaults) so they can be overridden per-environment without code changes.
"""
import os

# ─────────────────────────────────────────────────────────────
# AUDIO PROCESSING — must match training pipeline exactly
# ─────────────────────────────────────────────────────────────

STANDARD_SAMPLE_RATE: int = int(os.environ.get("STANDARD_SAMPLE_RATE", "16000"))
"""Target sample rate in Hz. All audio is resampled to this value."""

AUDIO_FIXED_SECONDS: int = int(os.environ.get("AUDIO_FIXED_SECONDS", "5"))
"""All audio is padded or truncated to exactly this many seconds."""

AUDIO_FIXED_SAMPLES: int = STANDARD_SAMPLE_RATE * AUDIO_FIXED_SECONDS
"""Derived: total number of samples per clip = 16000 × 5 = 80,000."""

# ─────────────────────────────────────────────────────────────
# LABEL CONTRACT — index order MUST match training-time assignment
# ─────────────────────────────────────────────────────────────

MODEL_LABELS: list[str] = os.environ.get("MODEL_LABELS", "real,fake").split(",")
"""
Label list ordered by model output index.
  index 0 → real
  index 1 → fake
Never change this order after training without retraining all models.
"""

LABEL_REAL: str = MODEL_LABELS[0]   # "real"
LABEL_FAKE: str = MODEL_LABELS[1]   # "fake"

LABEL_TO_INDEX: dict[str, int] = {label: i for i, label in enumerate(MODEL_LABELS)}
INDEX_TO_LABEL: dict[int, str] = {i: label for i, label in enumerate(MODEL_LABELS)}

# ─────────────────────────────────────────────────────────────
# MODEL REGISTRY — 4 data batches × 2 feature types = 8 models
# ─────────────────────────────────────────────────────────────

MODEL_BATCHES: list[str] = ["data3", "data5", "data6", "data8"]
"""The 4 disjoint training data splits. Each has its own pair of models."""

MODEL_FEATURES: list[str] = ["mel", "lfcc"]
"""The 2 feature types used to train independent ResNet18 models."""

TOTAL_MODEL_COUNT: int = len(MODEL_BATCHES) * len(MODEL_FEATURES)
"""Total number of models loaded at startup: 4 × 2 = 8."""

# Batch number suffix extracted from folder name (e.g. "data3" → "3")
_BATCH_SUFFIX: dict[str, str] = {b: b.replace("data", "") for b in MODEL_BATCHES}

def get_model_filename(feature: str, batch: str) -> str:
    """
    Return the .pth filename for a given (feature, batch) combination.

    Examples:
        get_model_filename("mel",  "data3") → "best_resnet18_mel_3.pth"
        get_model_filename("lfcc", "data8") → "best_resnet18_lfcc_8.pth"
    """
    return f"best_resnet18_{feature}_{_BATCH_SUFFIX[batch]}.pth"


def get_model_weight_path(feature: str, batch: str, weights_root: str = "ml/weights") -> str:
    """
    Return the full relative path to a model weight file.

    Example:
        get_model_weight_path("mel", "data3") → "ml/weights/data3/models/best_resnet18_mel_3.pth"
    """
    filename = get_model_filename(feature, batch)
    return f"{weights_root}/{batch}/models/{filename}"


# ─────────────────────────────────────────────────────────────
# FILE UPLOAD LIMITS
# ─────────────────────────────────────────────────────────────

MAX_UPLOAD_SIZE_MB: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_AUDIO_EXTENSIONS: frozenset[str] = frozenset({".wav", ".mp3", ".flac"})
ALLOWED_AUDIO_MIME_TYPES: frozenset[str] = frozenset({
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/flac",
    "audio/x-flac",
})
