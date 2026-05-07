"""
ml/preprocessing/audio_io.py

Audio loading — ported from DeepfakePipeline.__getitem__ (Cell 11, training notebook).

Training used: librosa.load(file_path, sr=16000)
Backend equivalent: load from raw bytes buffer using the same librosa call.

DO NOT change sr, mono behaviour, or dtype — these must match training exactly.
"""
import io
import logging

import librosa
import numpy as np

from ml.utils.exceptions import AudioLoadError

logger = logging.getLogger("ml")

# Must match training: self.sr = 16000
TARGET_SR: int = 16000


def load_audio_from_bytes(audio_bytes: bytes) -> np.ndarray:
    """
    Decode raw audio bytes → float32 mono waveform at 16 kHz.

    Mirrors the training pipeline's:
        wave, sr = librosa.load(file_path, sr=self.sr)

    librosa.load() automatically:
      - resamples to sr=16000
      - converts multi-channel to mono (mono=True by default)
      - returns float32 numpy array

    Args:
        audio_bytes: Raw bytes of an audio file (.wav, .mp3, .flac, etc.)

    Returns:
        np.ndarray of shape (N,) — float32 mono waveform at 16 kHz.

    Raises:
        AudioLoadError: If the file cannot be decoded.
    """
    try:
        buf = io.BytesIO(audio_bytes)
        wave, sr = librosa.load(buf, sr=TARGET_SR)
    except Exception as exc:
        raise AudioLoadError(f"Failed to decode audio: {exc}") from exc

    if wave is None or len(wave) == 0:
        raise AudioLoadError("Audio decoded to empty waveform.")

    logger.debug("Audio loaded: %d samples @ %d Hz (%.2fs)", len(wave), sr, len(wave) / sr)
    return wave

def get_audio_duration(audio_bytes: bytes) -> float:
    """Fast check for audio duration in seconds without full decode."""
    try:
        import soundfile as sf
        buf = io.BytesIO(audio_bytes)
        info = sf.info(buf)
        return info.duration
    except Exception as exc:
        # Fallback to librosa if soundfile fails
        try:
            buf = io.BytesIO(audio_bytes)
            return librosa.get_duration(path=buf)
        except Exception as e:
            raise AudioLoadError(f"Failed to get audio duration: {e}") from e

