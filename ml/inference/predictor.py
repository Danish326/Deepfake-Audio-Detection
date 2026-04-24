"""
ml/inference/predictor.py

Main prediction service — the single entry point the API layer calls.

Orchestrates:
    1. Preprocessing (audio → mel tensor + lfcc tensor)
    2. Inference on all 8 models
    3. Most-confident-wins aggregation
    4. Return AggregatedResult

This is the only file in ml/ that the FastAPI routes should import.
"""
import logging
import time
from typing import List

import torch

from ml.preprocessing.pipeline import preprocess
from ml.inference.model_registry import get_model
from ml.inference.cpu_runner import run_inference
from ml.inference.aggregator import SingleModelOutput, AggregatedResult, aggregate
from ml.utils.constants import MODEL_BATCHES, MODEL_FEATURES
from ml.utils.exceptions import ModelNotLoadedError

logger = logging.getLogger("ml")


def predict(audio_bytes: bytes) -> AggregatedResult:
    """
    Run the full deepfake detection pipeline on raw audio bytes.

    Steps:
        1. Preprocess audio → (mel_tensor, lfcc_tensor)
        2. For each of 8 models: run inference → softmax probs
        3. Aggregate → most-confident-wins

    Args:
        audio_bytes: Raw bytes of an uploaded audio file.

    Returns:
        AggregatedResult containing final label, confidence, winning model,
        and full per-model breakdown (all 8 outputs).

    Raises:
        AudioLoadError:        If audio cannot be decoded.
        FeatureExtractionError: If Mel/LFCC extraction fails.
        ModelNotLoadedError:   If all models are unavailable.
    """
    t_start = time.perf_counter()

    # ── Step 1: Preprocessing ────────────────────────────────
    t0 = time.perf_counter()
    features = preprocess(audio_bytes)
    t_preprocess = (time.perf_counter() - t0) * 1000
    logger.debug("Preprocessing: %.1f ms", t_preprocess)

    # Add batch dimension for model input: (1, C, H, W)
    mel_input  = features.mel_tensor.unsqueeze(0)   # (1, 1, 128, T)
    lfcc_input = features.lfcc_tensor.unsqueeze(0)  # (1, 1, T, 60)

    # ── Step 2: Run all 8 models ─────────────────────────────
    t0 = time.perf_counter()
    outputs: List[SingleModelOutput] = []

    feature_tensor_map = {
        "mel":  mel_input,
        "lfcc": lfcc_input,
    }

    for batch in MODEL_BATCHES:
        for feature in MODEL_FEATURES:
            try:
                model = get_model(batch, feature)
                tensor = feature_tensor_map[feature]
                probs = run_inference(model, tensor)   # (2,) [P(real), P(fake)]

                outputs.append(SingleModelOutput(
                    batch=batch,
                    feature=feature,
                    prob_real=float(probs[0]),
                    prob_fake=float(probs[1]),
                ))
            except ModelNotLoadedError:
                logger.warning("Skipping model (%s, %s) — not loaded.", batch, feature)
            except Exception as exc:
                logger.error(
                    "Inference error for (%s, %s): %s", batch, feature, exc
                )

    t_inference = (time.perf_counter() - t0) * 1000
    logger.debug("Inference (all %d models): %.1f ms", len(outputs), t_inference)

    if not outputs:
        raise ModelNotLoadedError(
            "All models failed or are unavailable. Cannot produce a prediction."
        )

    # ── Step 3: Aggregate ────────────────────────────────────
    result = aggregate(outputs)

    t_total = (time.perf_counter() - t_start) * 1000
    logger.info(
        "Prediction: label=%s  confidence=%.4f  winner=%s  "
        "models_ran=%d  total_ms=%.1f  preprocess_ms=%.1f  inference_ms=%.1f",
        result.label, result.confidence, result.winning_model,
        len(outputs), t_total, t_preprocess, t_inference,
    )

    return result
