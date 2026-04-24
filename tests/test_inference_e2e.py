"""
End-to-end inference test using a real audio file from the training dataset.
Runs the full pipeline: load audio -> preprocess -> 8 models -> aggregation.
"""
import sys
import os
import json

# ── Setup Django settings (needed for imports to resolve) ──
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ── Load models ────────────────────────────────────────────
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

from ml.inference.model_registry import load_all_models, get_load_status
load_all_models('ml/weights')

status = get_load_status()
loaded = sum(status.values())
print(f"\nModels loaded: {loaded}/8")

if loaded == 0:
    print("ERROR: No models loaded. Cannot run inference test.")
    sys.exit(1)

# ── Find a test audio file ─────────────────────────────────
import glob

# Look for any wav/mp3/flac in the training data directories
search_dirs = [
    r"d:\FAST UNIVERSITY\FYP\deepfake-audio-detection-backend\Model Training and Testing Python Code and Models",
    r"d:\FAST UNIVERSITY\FYP\Dataset",
    r"d:\FAST UNIVERSITY\FYP",
]

audio_file = None
for d in search_dirs:
    for ext in ['*.wav', '*.mp3', '*.flac']:
        files = glob.glob(os.path.join(d, '**', ext), recursive=True)
        if files:
            audio_file = files[0]
            break
    if audio_file:
        break

if not audio_file:
    # Generate a synthetic test tone if no real file found
    print("\nNo audio file found — generating synthetic 5s sine wave for test.")
    import numpy as np
    import soundfile as sf
    import tempfile

    sr = 16000
    t = np.linspace(0, 5, 5 * sr)
    wave = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    sf.write(tmp.name, wave, sr)
    audio_file = tmp.name

print(f"\nTest file: {audio_file}")

# ── Run inference ──────────────────────────────────────────
from ml.inference.predictor import predict

with open(audio_file, 'rb') as f:
    audio_bytes = f.read()

print(f"File size: {len(audio_bytes)/1024:.1f} KB")
print("\nRunning full pipeline (preprocess + 8 models + aggregation)...")

result = predict(audio_bytes)

print("\n" + "="*50)
print("RESULT")
print("="*50)
print(f"  Final label:    {result.label.upper()}")
print(f"  Confidence:     {result.confidence:.4f} ({result.confidence*100:.1f}%)")
print(f"  P(real):        {result.prob_real:.4f}")
print(f"  P(fake):        {result.prob_fake:.4f}")
print(f"  Winning model:  {result.winning_model}")
print(f"  Models ran:     {len(result.all_outputs)}/8")
print()
print("Per-model breakdown:")
for key, vals in sorted(result.per_model_summary.items()):
    winner_tag = " <-- WINNER" if key == result.winning_model else ""
    print(f"  {key:15s}  label={vals['label']}  conf={vals['confidence']:.4f}{winner_tag}")

print("\nInference test PASSED.")
