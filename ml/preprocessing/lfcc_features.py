"""
ml/preprocessing/lfcc_features.py

LFCC extraction — ported verbatim from DeepfakePipeline.__getitem__
(Cell 11, training notebook).

Training code (exact):
    lfcc_params = {'num_ceps': 60, 'nfilts': 128, 'nfft': 2048}

    from spafe.features.lfcc import lfcc
    lfcc_features = lfcc(
        sig=waveform_np,
        fs=self.sr,
        num_ceps=self.lfcc_params['num_ceps'],
        nfilts=self.lfcc_params['nfilts'],
        nfft=self.lfcc_params['nfft']
    )
    lfcc_features = (lfcc_features - lfcc_features.mean()) / (lfcc_features.std() + 1e-6)
    lfcc_tensor = torch.from_numpy(lfcc_features).unsqueeze(0).float()

CRITICAL: Training used the `spafe` library — NOT torchaudio. Using any other
library or different default parameters will produce completely different features
and silently break the model.

DO NOT change any parameter — must match training exactly.
"""
import logging

import numpy as np
import torch
from spafe.features.lfcc import lfcc as spafe_lfcc

from ml.utils.exceptions import FeatureExtractionError

logger = logging.getLogger("ml")

# Must match training: self.lfcc_params
LFCC_PARAMS: dict = {'num_ceps': 60, 'nfilts': 128, 'nfft': 2048}
SR: int = 16000


def extract_lfcc(waveform_np: np.ndarray) -> torch.Tensor:
    """
    Extract LFCC features from a standardised waveform using spafe.

    Args:
        waveform_np: float32 mono waveform, exactly 80,000 samples.

    Returns:
        torch.Tensor of shape (1, T, 60) — float32, z-score normalised.

    Raises:
        FeatureExtractionError: If extraction fails or produces invalid output.
    """
    try:
        lfcc_features = spafe_lfcc(
            sig=waveform_np,
            fs=SR,
            num_ceps=LFCC_PARAMS['num_ceps'],
            nfilts=LFCC_PARAMS['nfilts'],
            nfft=LFCC_PARAMS['nfft']
        )
        lfcc_features = (lfcc_features - lfcc_features.mean()) / (lfcc_features.std() + 1e-6)
        lfcc_tensor = torch.from_numpy(lfcc_features).unsqueeze(0).float()
    except Exception as exc:
        raise FeatureExtractionError(f"LFCC extraction failed: {exc}") from exc

    logger.debug("LFCC tensor shape: %s", lfcc_tensor.shape)
    return lfcc_tensor
