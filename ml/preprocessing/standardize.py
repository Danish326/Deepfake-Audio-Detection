"""
ml/preprocessing/standardize.py

Pad/truncate waveform to exactly 5 seconds — ported verbatim from
DeepfakePipeline.__getitem__ (Cell 11, training notebook).

Training code (exact):
    self.target_len = int(5.0 * self.sr)   # 80000

    if current_len < self.target_len:
        n_repeats = int(np.ceil(self.target_len / current_len))
        wave = np.tile(wave, n_repeats)[:self.target_len]
    elif current_len > self.target_len:
        wave = wave[:self.target_len]

DO NOT change padding/truncation strategy — must match training exactly.
"""
import logging

import numpy as np

logger = logging.getLogger("ml")

# Must match: self.target_len = int(5.0 * 16000) = 80000
TARGET_LEN: int = 80_000


def pad_or_truncate(wave: np.ndarray) -> np.ndarray:
    """
    Ensure waveform is exactly TARGET_LEN (80,000) samples.

    - Shorter → tile-repeat then front-truncate  (training strategy)
    - Longer  → front-truncate                   (training strategy)
    - Equal   → return unchanged

    Args:
        wave: float32 mono waveform, any length.

    Returns:
        np.ndarray of shape (80000,).
    """
    current_len = len(wave)

    if current_len < TARGET_LEN:
        n_repeats = int(np.ceil(TARGET_LEN / current_len))
        wave = np.tile(wave, n_repeats)[:TARGET_LEN]
    elif current_len > TARGET_LEN:
        wave = wave[:TARGET_LEN]

    assert len(wave) == TARGET_LEN, f"Expected {TARGET_LEN} samples, got {len(wave)}"
    logger.debug("Standardized waveform to %d samples", TARGET_LEN)
    return wave
