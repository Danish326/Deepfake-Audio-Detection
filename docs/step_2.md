# Step 2 — ML Integration

> **Status**: ✅ Implemented
>
> **Phase mapping**: Phase 2 from the spec (`project-software-specification.md`)
>
> **Implementation Decision**: Code is ported **verbatim** from the training notebook. No refactoring or rewrites of ML logic. Classes (`MelResNet18`, `LFCCResNet18`), preprocessing functions, and feature extraction are used exactly as they appear in `Audio Deepfake Detection - FYP PHASE 1 Completed.ipynb`.

---

## ✅ Implementation Summary

| File | Result |
|---|---|
| `ml/models/mel_resnet18.py` | ✅ `MelResNet18` — verbatim from notebook Cell 13 |
| `ml/models/lfcc_resnet18.py` | ✅ `LFCCResNet18` — verbatim from notebook Cell 13 |
| `ml/preprocessing/audio_io.py` | ✅ `librosa.load(sr=16000)` — exact training loader |
| `ml/preprocessing/standardize.py` | ✅ Tile-repeat pad + front-truncate |
| `ml/preprocessing/mel_features.py` | ✅ n_mels=128, hop=512, n_fft=2048, power_to_db, z-score |
| `ml/preprocessing/lfcc_features.py` | ✅ `spafe.lfcc()` num_ceps=60, nfilts=128, nfft=2048, z-score |
| `ml/preprocessing/pipeline.py` | ✅ Orchestrates load → standardize → mel + lfcc |
| `ml/inference/model_registry.py` | ✅ Loads all 8 `.pth` files; logs clear error per missing model |
| `ml/inference/cpu_runner.py` | ✅ `torch.no_grad()` + `softmax` wrapper |
| `ml/inference/aggregator.py` | ✅ Most-confident-wins; returns full 8-model breakdown |
| `ml/inference/predictor.py` | ✅ End-to-end: preprocess → 8 inferences → aggregate |
| `ml/utils/exceptions.py` | ✅ `AudioLoadError`, `FeatureExtractionError`, `ModelLoadError` |
| `api/fastapi_app.py` | ✅ Added `lifespan` hook — loads all 8 models at startup |
| `api/routes/health.py` | ✅ Now reads real load status from registry |
| `requirements.txt` | ✅ Added torch, torchaudio, torchvision, librosa, spafe, soundfile |

### Verification Results (with real .pth files)

#### Bug Found & Fixed: Lifespan Hook
When FastAPI is mounted inside Starlette's `Mount()`, the inner FastAPI lifespan does **not** fire. Fixed by moving `load_all_models()` into the outer Starlette app lifespan in `config/asgi.py`.

#### Startup Log
```
[INFO] api [startup] Loading ML models from ml/weights ...
[INFO] ml  Loaded model: data3/mel  ✓
[INFO] ml  Loaded model: data3/lfcc ✓
[INFO] ml  Loaded model: data5/mel  ✓
[INFO] ml  Loaded model: data5/lfcc ✓
[INFO] ml  Loaded model: data6/mel  ✓
[INFO] ml  Loaded model: data6/lfcc ✓
[INFO] ml  Loaded model: data8/mel  ✓
[INFO] ml  Loaded model: data8/lfcc ✓
[INFO] ml  Model registry: 8/8 models loaded.
```

#### Health Endpoint (live, with models)
```
GET /api/v1/health → 200 OK
status: "ok"  (all 8 model flags = true)
```

#### End-to-End Inference (real 625 KB .wav audio file)
```
Final label:    REAL
Confidence:     1.0000 (100.0%)
Winning model:  mel_data3
Models ran:     8/8

Per-model breakdown:
  mel_data3   → real  1.0000  <-- WINNER
  lfcc_data3  → real  0.9997
  mel_data8   → real  0.9883
  mel_data6   → real  0.9853
  lfcc_data8  → real  0.8296
  lfcc_data5  → real  0.6648
  lfcc_data6  → real  0.6026
  mel_data5   → fake  0.9276  (dissenting — overruled by mel_data3)

Inference test PASSED.
```

> **Note on step 3**: There is no HTTP upload endpoint yet. The `predict()` function works
> but is only callable directly. Step 3 adds `POST /api/v1/predict/audio`.

---

## What Will Be Built in This Step

This step ports the **exact training pipeline** from the Jupyter notebook into the backend's `ml/` package. By the end of this step, the backend will be able to:

1. Load all **8 trained ResNet18 models** into memory at startup
2. Accept a raw audio waveform and run the **complete preprocessing pipeline**
3. Run all 8 models and apply the **most-confident-wins aggregation**
4. Return a structured `PredictionResult` object to the route layer
5. Report real model load status in the **`/api/v1/health` endpoint**

No new API endpoints are created in this step (that's Step 3). This step is purely about the ML engine.

---

## Key Findings from the Training Notebook

The Jupyter notebook (`Audio Deepfake Detection - FYP PHASE 1 Completed.ipynb`) was fully read and all critical training-time parameters were extracted. These are now locked — any deviation will silently degrade accuracy.

### Exact Preprocessing Parameters

| Parameter | Value | Source |
|---|---|---|
| Sample rate | **16,000 Hz** | `self.sr = 16000` |
| Fixed audio length | **5 seconds** → 80,000 samples | `self.target_len = int(5.0 * self.sr)` |
| Audio loader | **`librosa.load(sr=16000)`** | `wave, sr = librosa.load(file_path, sr=self.sr)` |
| Silence trim | **None during training** — librosa loads pre-segmented clips from CSV | Dataset uses `start`/`end` columns |
| Padding strategy | **Tile-repeat then truncate** | `np.tile(wave, n_repeats)[:target_len]` |
| Truncation strategy | **Front-truncate** | `wave = wave[:self.target_len]` |

### Exact Mel-Spectrogram Parameters

```python
mel_params = {'n_mels': 128, 'hop_length': 512, 'n_fft': 2048}

mel = librosa.feature.melspectrogram(y=waveform_np, sr=16000, **mel_params)
mel_db = librosa.power_to_db(mel, ref=np.max)

# Per-sample z-score normalisation (no global stats file used at inference)
mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)

# Add channel dim → shape: (1, 128, T)
mel_tensor = torch.from_numpy(mel_db).unsqueeze(0).float()
```

### Exact LFCC Parameters

```python
lfcc_params = {'num_ceps': 60, 'nfilts': 128, 'nfft': 2048}

# Uses spafe library (not torchaudio)
from spafe.features.lfcc import lfcc as spafe_lfcc

lfcc_features = spafe_lfcc(sig=waveform_np, fs=16000,
                            num_ceps=60, nfilts=128, nfft=2048)

# Per-sample z-score normalisation
lfcc_features = (lfcc_features - lfcc_features.mean()) / (lfcc_features.std() + 1e-6)

# Add channel dim → shape: (1, T, 60)
lfcc_tensor = torch.from_numpy(lfcc_features).unsqueeze(0).float()
```

### Model Architecture (identical for Mel and LFCC)

```python
# Both MelResNet18 and LFCCResNet18 have IDENTICAL architecture
# The only difference is their trained weights

from torchvision.models import resnet18
import torch.nn as nn

class AudioResNet18(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.model = resnet18(weights=None)

        # 1-channel input (spectrogram / LFCC) instead of 3-channel RGB
        self.model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)

        # Dropout before final layer
        self.dropout = nn.Dropout(0.3)

        # 2-class output: [real, fake]
        self.model.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.model.conv1(x)
        x = self.model.bn1(x)
        x = self.model.relu(x)
        x = self.model.maxpool(x)
        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)
        x = self.model.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.model.fc(x)
        return x
```

### Checkpoint Format

```python
# .pth files are saved as full checkpoints, not bare state dicts:
checkpoint = torch.load(model_path, map_location="cpu")
state_dict = checkpoint['model_state_dict']   # ← key is 'model_state_dict'

# NO prefix removal needed for the final saved models
# (the commented-out code in testing shows prefix removal was only for an older format)
model.load_state_dict(state_dict)
```

### Label Contract

```
index 0 → real
index 1 → fake

softmax → probs[0] = P(real),  probs[1] = P(fake)
```

---

## Files That Will Be Created / Modified

```
ml/
├── models/
│   ├── __init__.py          (already exists)
│   └── resnet18.py          [NEW] Single AudioResNet18 class used for both features
│
├── preprocessing/
│   ├── __init__.py          (already exists)
│   ├── audio_io.py          [NEW] librosa.load wrapper + validation
│   ├── standardize.py       [NEW] pad/truncate to exactly 5s (80,000 samples)
│   ├── mel_features.py      [NEW] Mel-spectrogram extraction (exact training params)
│   ├── lfcc_features.py     [NEW] LFCC extraction via spafe (exact training params)
│   └── pipeline.py          [NEW] Orchestrates full preprocessing → returns (mel_tensor, lfcc_tensor)
│
├── inference/
│   ├── __init__.py          (already exists)
│   ├── model_registry.py    [NEW] Loads & holds all 8 models in memory at startup
│   ├── cpu_runner.py        [NEW] torch.no_grad() inference wrapper for a single model
│   ├── aggregator.py        [NEW] Most-confident-wins selection across 8 outputs
│   └── predictor.py         [NEW] Main service: orchestrates preprocessing + 8 inferences + aggregation
│
└── utils/
    ├── __init__.py          (already exists)
    ├── constants.py         (already exists — no changes needed)
    └── exceptions.py        [NEW] ML-specific exception types

api/
└── routes/
    └── health.py            [MODIFY] Reads real model load status from model_registry

requirements.txt             [MODIFY] Add torch, torchaudio, librosa, spafe, numpy
```

---

## Component Details

### `ml/models/resnet18.py`
Single `AudioResNet18` class — identical architecture for both features. Both Mel and LFCC models are loaded using this same class with their respective `.pth` weight files.

### `ml/preprocessing/audio_io.py`
Wraps `librosa.load()` to:
- Accept a raw bytes buffer (uploaded file content)
- Decode to float32 waveform at `sr=16000` (resamples automatically)
- Convert multi-channel to mono (librosa does this by default with `mono=True`)
- Return `waveform: np.ndarray` of shape `(N,)`

> **No silence trimming** — the training pipeline loaded pre-segmented clips. Applying silence trimming at inference would create a train/serve mismatch.

### `ml/preprocessing/standardize.py`
Pad or truncate the waveform to exactly **80,000 samples** (5s × 16kHz):
- If shorter: **tile-repeat then truncate** (matches training)
- If longer: **front-truncate** (matches training)

### `ml/preprocessing/mel_features.py`
```python
mel = librosa.feature.melspectrogram(y=wave, sr=16000, n_mels=128, hop_length=512, n_fft=2048)
mel_db = librosa.power_to_db(mel, ref=np.max)
mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
tensor = torch.from_numpy(mel_db).unsqueeze(0).float()  # → (1, 128, T)
```

### `ml/preprocessing/lfcc_features.py`
```python
from spafe.features.lfcc import lfcc as spafe_lfcc
feats = spafe_lfcc(sig=wave, fs=16000, num_ceps=60, nfilts=128, nfft=2048)
feats = (feats - feats.mean()) / (feats.std() + 1e-6)
tensor = torch.from_numpy(feats).unsqueeze(0).float()  # → (1, T, 60)
```

### `ml/inference/model_registry.py`
Loads all 8 models at application startup:

```python
REGISTRY: dict[tuple[str, str], AudioResNet18] = {}

def load_all_models(weights_root: str) -> None:
    for batch in ["data3", "data5", "data6", "data8"]:
        for feature in ["mel", "lfcc"]:
            path = get_model_weight_path(feature, batch, weights_root)
            model = AudioResNet18(num_classes=2)
            checkpoint = torch.load(path, map_location="cpu")
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()
            REGISTRY[(batch, feature)] = model
```

Exposed via a `get_registry()` function so FastAPI's startup event can call it once.

### `ml/inference/aggregator.py`
Most-confident-wins selection:

```python
# For each model i, compute:
#   confidence_i = max(P_i(real), P_i(fake))
# Winner = the model with highest confidence_i
# Final result = winner's label + confidence + all 8 per-model outputs
```

### `ml/inference/predictor.py`
Main prediction service — the only entry point the API layer calls:

```python
def predict(audio_bytes: bytes) -> PredictionResult:
    waveform = load_audio(audio_bytes)         # decode → mono float32 @ 16kHz
    waveform = standardize(waveform)           # pad/truncate → 80,000 samples
    mel_tensor  = extract_mel(waveform)        # → (1, 128, T) tensor
    lfcc_tensor = extract_lfcc(waveform)       # → (1, T, 60) tensor

    all_outputs = []
    for batch in BATCHES:
        for feature, tensor in [("mel", mel_tensor), ("lfcc", lfcc_tensor)]:
            logits = run_model(REGISTRY[(batch, feature)], tensor)
            probs  = softmax(logits)
            all_outputs.append(ModelOutput(batch, feature, probs))

    return aggregate(all_outputs)  # most-confident-wins
```

### Updated `api/routes/health.py`
Will import `model_registry.get_load_status()` and return real `True/False` per model instead of the current all-False stub.

---

## Dependencies Added in This Step

```diff
# requirements.txt additions

+ torch>=2.2,<3.0
+ torchaudio>=2.2,<3.0
+ torchvision>=0.17,<1.0
+ numpy>=1.26,<3.0
+ librosa>=0.10,<1.0
+ spafe>=0.3,<1.0
+ soundfile>=0.12,<1.0
```

> **Note on `spafe`**: The LFCC computation in the training notebook uses `spafe.features.lfcc.lfcc()`. This library must be used — torchaudio's LFCC implementation uses different default parameters and would produce different features, breaking the model.

---

## FastAPI Startup Integration

The model registry needs to load all 8 models when the server starts, not on the first request. This is done via FastAPI's lifespan context manager in `api/fastapi_app.py`:

```python
from contextlib import asynccontextmanager
from ml.inference.model_registry import load_all_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load all 8 models
    load_all_models(weights_root="ml/weights")
    yield
    # Shutdown: nothing to clean up (models are released with the process)

app = FastAPI(..., lifespan=lifespan)
```

---

## What Is Explicitly NOT Done in This Step

- No HTTP upload endpoint (`POST /api/v1/predict/audio`) — that is Step 3
- No database persistence of predictions — that is Step 4
- No authentication — that is Step 5
- No augmentation at inference (augmentation was training-only)
- No GPU support (CPU-only, architecture abstracts `device`)

---

## Success Criteria for This Step

- [ ] `uvicorn config.asgi:application --reload` starts and logs all 8 models loaded
- [ ] `GET /api/v1/health` returns real `True` for each model that loaded successfully
- [ ] `predict(audio_bytes)` returns correct label + confidence for a test `.wav` file
- [ ] Mel tensor shape is `(1, 1, 128, T)` (batch dim added for model input)
- [ ] LFCC tensor shape is `(1, 1, T, 60)` (batch dim added for model input)
- [ ] Most-confident-wins selects the correct winner from a known set of outputs
- [ ] If a model `.pth` file is missing, startup logs a clear error (no silent failures)
- [ ] Unit tests pass for: `standardize()`, `extract_mel()`, `extract_lfcc()`, `aggregate()`

---

> ✅ **Approve this step to begin implementation.**
> Once implemented, this file will be updated with a summary of what was actually built and any deviations from the plan.
