"""
ml/inference/aggregator.py

Most-confident-wins aggregation across all 8 model outputs.

Strategy (from a_little_change.md):
    All model outputs (confidence scores / softmax probabilities) are collected
    and the MOST CONFIDENT prediction across all 8 models is selected as the
    final result shown to the user.

For each model i:
    confidence_i = max(P_i(real), P_i(fake))
    label_i      = "real" if P_i(real) > P_i(fake) else "fake"

Winner = model with highest confidence_i
Final label      = label_winner
Final confidence = confidence_winner
"""
import logging
from dataclasses import dataclass, field
from typing import List

import torch

logger = logging.getLogger("ml")


@dataclass
class SingleModelOutput:
    """Prediction output from a single model."""
    batch: str          # e.g. "data3"
    feature: str        # "mel" or "lfcc"
    prob_real: float    # P(real)
    prob_fake: float    # P(fake)

    @property
    def confidence(self) -> float:
        return max(self.prob_real, self.prob_fake)

    @property
    def label(self) -> str:
        return "real" if self.prob_real > self.prob_fake else "fake"

    @property
    def model_key(self) -> str:
        return f"{self.feature}_{self.batch}"


@dataclass
class AggregatedResult:
    """Final aggregated prediction returned to the API layer."""
    label: str                           # "real" or "fake"
    confidence: float                    # winner's max(P(real), P(fake))
    prob_real: float                     # winner's P(real)
    prob_fake: float                     # winner's P(fake)
    winning_model: str                   # e.g. "mel_data3"
    all_outputs: List[SingleModelOutput] = field(default_factory=list)

    @property
    def per_model_summary(self) -> dict:
        """Compact dict of all 8 model outputs for API response / logging."""
        return {
            o.model_key: {
                "label": o.label,
                "confidence": round(o.confidence, 4),
                "prob_real": round(o.prob_real, 4),
                "prob_fake": round(o.prob_fake, 4),
            }
            for o in self.all_outputs
        }


def aggregate(outputs: List[SingleModelOutput]) -> AggregatedResult:
    """
    Select the most confident prediction from a list of per-model outputs.

    Args:
        outputs: List of SingleModelOutput — one per model that ran successfully.
                 Must have at least 1 entry.

    Returns:
        AggregatedResult with the winning model's label and confidence.

    Raises:
        ValueError: If outputs list is empty.
    """
    if not outputs:
        raise ValueError("Cannot aggregate: no model outputs provided.")

    winner = max(outputs, key=lambda o: o.confidence)

    logger.debug(
        "Aggregation winner: %s  label=%s  confidence=%.4f",
        winner.model_key, winner.label, winner.confidence
    )

    return AggregatedResult(
        label=winner.label,
        confidence=round(winner.confidence, 4),
        prob_real=round(winner.prob_real, 4),
        prob_fake=round(winner.prob_fake, 4),
        winning_model=winner.model_key,
        all_outputs=outputs,
    )
