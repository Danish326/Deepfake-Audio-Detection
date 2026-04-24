"""
ml/preprocessing/mel_features.py

Mel-Spectrogram extraction — ported verbatim from DeepfakePipeline.__getitem__
(Cell 11, training notebook).

Training code (exact):
    mel_params = {'n_mels': 128, 'hop_length': 512, 'n_fft': 2048}

    mel = librosa.feature.melspectrogram(
        y=waveform_np, sr=self.sr, **mel_params
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
    mel_tensor = torch.from_numpy(mel_db).unsqueeze(0).float()

DO NOT change any parameter — must match training exactly.
"""
import logging

import librosa
import numpy as np
import torch

from ml.utils.exceptions import FeatureExtractionError

logger = logging.getLogger("ml")

# Must match training: self.mel_params
MEL_PARAMS: dict = {'n_mels': 128, 'hop_length': 512, 'n_fft': 2048}
SR: int = 16000


def extract_mel(waveform_np: np.ndarray) -> torch.Tensor:
    """
    Extract Mel-Spectrogram from a standardised waveform.

    Args:
        waveform_np: float32 mono waveform, exactly 80,000 samples.

    Returns:
        torch.Tensor of shape (1, 128, T) — float32, z-score normalised.

    Raises:
        FeatureExtractionError: If extraction fails or produces invalid output.
    """
    try:
        mel = librosa.feature.melspectrogram(
            y=waveform_np,
            sr=SR,
            **MEL_PARAMS
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
        mel_tensor = torch.from_numpy(mel_db).unsqueeze(0).float()
    except Exception as exc:
        raise FeatureExtractionError(f"Mel extraction failed: {exc}") from exc

    logger.debug("Mel tensor shape: %s", mel_tensor.shape)
    return mel_tensor
