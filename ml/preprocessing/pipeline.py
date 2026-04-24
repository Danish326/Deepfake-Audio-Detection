"""
ml/preprocessing/pipeline.py

Full preprocessing pipeline — orchestrates all steps in the exact order
used during training.

Steps (matching DeepfakePipeline.__getitem__, Cell 11):
    1. Load audio bytes → float32 mono waveform @ 16 kHz
    2. Pad or truncate → exactly 80,000 samples
    3. Extract Mel-Spectrogram tensor  → (1, 128, T)
    4. Extract LFCC tensor             → (1, T, 60)

Returns both tensors together so the inference layer can feed each to
its respective model without re-running audio loading.
"""
import logging
from dataclasses import dataclass

import numpy as np
import torch

from ml.preprocessing.audio_io import load_audio_from_bytes
from ml.preprocessing.standardize import pad_or_truncate
from ml.preprocessing.mel_features import extract_mel
from ml.preprocessing.lfcc_features import extract_lfcc

logger = logging.getLogger("ml")


@dataclass
class PreprocessedFeatures:
    """Holds the two feature tensors produced by the preprocessing pipeline."""
    mel_tensor: torch.Tensor   # shape: (1, 128, T)
    lfcc_tensor: torch.Tensor  # shape: (1, T, 60)
    waveform: np.ndarray       # shape: (80000,) — kept for debugging


def preprocess(audio_bytes: bytes) -> PreprocessedFeatures:
    """
    Run the complete preprocessing pipeline on raw audio bytes.

    Args:
        audio_bytes: Raw bytes of an uploaded audio file.

    Returns:
        PreprocessedFeatures with mel and lfcc tensors ready for model input.

    Raises:
        AudioLoadError: If the file cannot be decoded.
        FeatureExtractionError: If Mel or LFCC extraction fails.
    """
    # Step 1: Load
    wave = load_audio_from_bytes(audio_bytes)

    # Step 2: Standardise to 5s
    wave = pad_or_truncate(wave)

    # Step 3 & 4: Extract features (both use the same standardised waveform)
    mel_tensor  = extract_mel(wave)
    lfcc_tensor = extract_lfcc(wave)

    logger.debug(
        "Preprocessing done — mel: %s  lfcc: %s",
        mel_tensor.shape,
        lfcc_tensor.shape,
    )
    return PreprocessedFeatures(
        mel_tensor=mel_tensor,
        lfcc_tensor=lfcc_tensor,
        waveform=wave,
    )
