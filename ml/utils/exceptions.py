"""
ml/utils/exceptions.py

ML-specific exception types.
"""


class AudioLoadError(Exception):
    """Raised when audio cannot be decoded or is completely silent after load."""


class FeatureExtractionError(Exception):
    """Raised when Mel or LFCC extraction produces an invalid tensor."""


class ModelLoadError(Exception):
    """Raised when a .pth weight file cannot be loaded at startup."""


class ModelNotLoadedError(Exception):
    """Raised when inference is attempted before models have been loaded."""


class QuotaExceededError(Exception):
    """Raised when a user exceeds their monthly prediction limit."""


class AudioTooLongError(Exception):
    """Raised when uploaded audio exceeds the max duration of the user's plan."""


class SubscriptionExpiredError(Exception):
    """Raised when a user's subscription is not active."""
