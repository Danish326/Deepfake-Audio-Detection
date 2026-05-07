# Deepfake Audio Detection Backend — Complete Project Detail

## 1. Project Overview

This backend detects whether an audio file is **real** or **AI-generated (deepfake)** using an ensemble of **8 ResNet18** deep learning models. It is built with **Django** (admin, ORM, auth) + **FastAPI** (inference API) mounted together under a single ASGI application, deployed via **Docker** with PostgreSQL and Nginx.

### How It Works (Simple Explanation)
1. A user uploads an audio file (`.wav`, `.mp3`, or `.flac`)
2. The audio is decoded, resampled to 16 kHz, and standardised to exactly 5 seconds
3. Two types of audio features are extracted: **Mel-Spectrogram** and **LFCC**
4. Each feature is passed through **4 independently trained ResNet18 models** (one per data batch)
5. All **8 model outputs** are compared — the **most confident** prediction wins
6. The result (`real` or `fake` + confidence score) is saved to the database and returned as JSON

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | Django 5.x | Admin panel, ORM, migrations, user auth |
| **API Framework** | FastAPI | Inference endpoints, Swagger docs, file uploads |
| **ASGI Server** | Uvicorn + Gunicorn | Production-grade async server |
| **ML Framework** | PyTorch (CPU) | ResNet18 model inference |
| **Audio Processing** | librosa, spafe, soundfile | Audio decoding & feature extraction |
| **Database** | PostgreSQL 15 (prod) / SQLite (dev) | Stores users, predictions, uploads |
| **Reverse Proxy** | Nginx | Routes traffic, serves static files |
| **Containerisation** | Docker + Docker Compose | Packages everything for deployment |
| **Authentication** | PyJWT | JSON Web Token auth for API endpoints |

---

## 3. Project Folder Structure

```
deepfake-audio-detection-backend/
│
├── manage.py                    # Django CLI entry point
├── requirements.txt             # All Python dependencies
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Multi-container orchestration
├── docker-entrypoint.sh         # Container startup script
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules
│
├── config/                      # Django project configuration
│   ├── asgi.py                  # ASGI entry — mounts Django + FastAPI
│   ├── urls.py                  # Django URL configuration
│   ├── wsgi.py                  # WSGI fallback
│   └── settings/
│       ├── __init__.py          # Auto-selects env via APP_ENV
│       ├── base.py              # Shared settings (all environments)
│       ├── local.py             # DEBUG=True, SQLite
│       ├── staging.py           # DEBUG=False, PostgreSQL
│       └── production.py        # Hardened production settings
│
├── api/                         # FastAPI application
│   ├── fastapi_app.py           # App factory — creates FastAPI instance
│   ├── dependencies.py          # get_current_user (JWT validation)
│   ├── middleware.py             # Request-ID + Timing middleware
│   ├── routes/
│   │   ├── health.py            # GET  /api/v1/health
│   │   ├── auth.py              # POST /api/v1/auth/login, GET /me
│   │   ├── predict.py           # POST /api/v1/predict/audio
│   │   └── predictions.py       # GET  /api/v1/predictions/history
│   └── schemas/
│       ├── common.py            # BaseResponse, ErrorResponse, HealthResponse
│       ├── predict.py           # PredictionResponse, PerModelOutput
│       └── auth.py              # LoginRequest, TokenResponse, UserResponse
│
├── apps/                        # Django applications
│   ├── users/
│   │   └── models.py            # Custom User model (UUID primary key)
│   ├── predictions/
│   │   ├── models.py            # Prediction + ModelRegistry models
│   │   ├── services.py          # create_prediction_record()
│   │   ├── selectors.py         # Query helpers for history endpoint
│   │   └── admin.py             # Read-only admin panels
│   ├── uploads/
│   │   └── models.py            # UploadedAudio model
│   └── audit_logs/              # Placeholder for future use
│
├── ml/                          # Machine Learning pipeline
│   ├── models/
│   │   ├── mel_resnet18.py      # MelResNet18 architecture class
│   │   └── lfcc_resnet18.py     # LFCCResNet18 architecture class
│   ├── preprocessing/
│   │   ├── audio_io.py          # Decode audio bytes → numpy waveform
│   │   ├── standardize.py       # Pad/truncate to exactly 5 seconds
│   │   ├── mel_features.py      # Mel-Spectrogram extraction
│   │   ├── lfcc_features.py     # LFCC extraction (via spafe library)
│   │   └── pipeline.py          # Orchestrates all preprocessing steps
│   ├── inference/
│   │   ├── model_registry.py    # Loads & stores all 8 models in memory
│   │   ├── cpu_runner.py        # torch.no_grad() inference wrapper
│   │   ├── aggregator.py        # Most-confident-wins selection
│   │   └── predictor.py         # Main entry point: preprocess → infer → aggregate
│   ├── utils/
│   │   ├── constants.py         # Frozen ML params, label contract, file limits
│   │   └── exceptions.py        # AudioLoadError, ModelNotLoadedError, etc.
│   └── weights/                 # Model weight files (git-ignored)
│       ├── data3/models/        # best_resnet18_mel_3.pth, best_resnet18_lfcc_3.pth
│       ├── data5/models/        # best_resnet18_mel_5.pth, best_resnet18_lfcc_5.pth
│       ├── data6/models/        # best_resnet18_mel_6.pth, best_resnet18_lfcc_6.pth
│       └── data8/models/        # best_resnet18_mel_8.pth, best_resnet18_lfcc_8.pth
│
├── nginx/
│   └── nginx.conf               # Reverse proxy configuration
│
├── tests/                       # Test suites
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── regression/
│   └── load/
│
├── media/                       # Uploaded files directory
├── logs/                        # Application logs
└── staticfiles/                 # Collected Django static files
```

---

## 4. ASGI Architecture — How Django + FastAPI Run Together

Both frameworks run in **one process** under a single ASGI application (`config/asgi.py`):

```
Incoming Request
      │
      ▼
┌─────────────────────────┐
│   Starlette Router      │   ← config/asgi.py
│   (lifespan: loads 8    │
│    ML models at startup)│
├─────────────────────────┤
│  /api/*  →  FastAPI     │   Inference API, Auth, Health
│  /*      →  Django      │   Admin panel, static files
└─────────────────────────┘
```

**Why this design?** FastAPI handles the ML inference routes efficiently with async support and auto-generated Swagger docs, while Django provides the battle-tested admin panel, ORM, and migration system. They share the same database.

**Key detail:** When FastAPI is mounted inside Starlette's `Mount()`, FastAPI's own lifespan hook does NOT fire. Therefore, model loading happens in the **outer Starlette lifespan** in `config/asgi.py`.

---

## 5. ML Pipeline — Deep Dive

### 5.1 The 8-Model Architecture

The dataset was split into **4 non-overlapping batches** (data3, data5, data6, data8). For each batch, **two models** were trained independently:

| Batch | Mel-Spectrogram Model | LFCC Model |
|-------|----------------------|------------|
| data3 | `best_resnet18_mel_3.pth` | `best_resnet18_lfcc_3.pth` |
| data5 | `best_resnet18_mel_5.pth` | `best_resnet18_lfcc_5.pth` |
| data6 | `best_resnet18_mel_6.pth` | `best_resnet18_lfcc_6.pth` |
| data8 | `best_resnet18_mel_8.pth` | `best_resnet18_lfcc_8.pth` |

**Total: 8 models** loaded at startup, all running on every request.

### 5.2 ResNet18 Model Architecture

Both `MelResNet18` and `LFCCResNet18` share identical architecture — only the trained weights differ:

```python
class AudioResNet18(nn.Module):
    def __init__(self, num_classes=2):
        self.model = resnet18(weights=None)
        self.model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)  # 1-channel input
        self.dropout = nn.Dropout(0.3)
        self.model.fc = nn.Linear(512, num_classes)  # 2-class output: [real, fake]
```

Key modifications from standard ResNet18:
- **Input:** 1 channel (spectrogram) instead of 3 channels (RGB)
- **Output:** 2 classes (real, fake) instead of 1000 (ImageNet)
- **Dropout:** 0.3 before the final fully-connected layer

### 5.3 Preprocessing Pipeline

Every audio file goes through this exact sequence (`ml/preprocessing/pipeline.py`):

```
Raw Audio Bytes
      │
      ▼
┌─────────────────────────────────────────┐
│ 1. audio_io.py: Decode Audio            │
│    librosa.load(bytes, sr=16000)        │
│    → float32 mono waveform @ 16 kHz     │
├─────────────────────────────────────────┤
│ 2. standardize.py: Pad / Truncate       │
│    Short audio → tile-repeat to 5s      │
│    Long audio  → truncate to 5s         │
│    → exactly 80,000 samples             │
├─────────────────────────────────────────┤
│ 3a. mel_features.py: Mel-Spectrogram    │
│     n_mels=128, hop=512, n_fft=2048     │
│     power_to_db → z-score normalise     │
│     → tensor shape: (1, 128, T)         │
├─────────────────────────────────────────┤
│ 3b. lfcc_features.py: LFCC             │
│     num_ceps=60, nfilts=128, nfft=2048  │
│     z-score normalise                   │
│     → tensor shape: (1, T, 60)          │
└─────────────────────────────────────────┘
```

**Critical rule:** Every parameter here was extracted from the training notebook and must **never** be changed. Any deviation silently breaks model accuracy.

### 5.4 Inference Flow

`ml/inference/predictor.py` is the single entry point:

```
predict(audio_bytes)
    │
    ├── preprocess(audio_bytes)      → mel_tensor, lfcc_tensor
    │
    ├── For each of 4 batches:
    │     ├── run_inference(mel_model,  mel_tensor)   → [P(real), P(fake)]
    │     └── run_inference(lfcc_model, lfcc_tensor)  → [P(real), P(fake)]
    │
    └── aggregate(8 outputs)         → AggregatedResult
```

### 5.5 Aggregation Strategy: Most-Confident-Wins

```python
# For each model i:
confidence_i = max(P_i(real), P_i(fake))
label_i      = "real" if P_i(real) > P_i(fake) else "fake"

# Winner = model with highest confidence
winner = max(all_models, key=lambda m: m.confidence)
final_label = winner.label
final_confidence = winner.confidence
```

This strategy picks the model that is **most sure** of its answer, regardless of what other models say.

### 5.6 Label Contract

```
index 0 → "real"     (genuine human speech)
index 1 → "fake"     (AI-generated / deepfake)
```

---

## 6. API Endpoints

### 6.1 Health Check
```
GET /api/v1/health

Response 200:
{
  "success": true,
  "status": "ok",              // "ok" or "degraded"
  "service": "deepfake-audio-backend",
  "models": {
    "mel_data3": true, "mel_data5": true, "mel_data6": true, "mel_data8": true,
    "lfcc_data3": true, "lfcc_data5": true, "lfcc_data6": true, "lfcc_data8": true
  },
  "database": "ok",
  "version": "1.0.0"
}
```

### 6.2 Authentication
```
POST /api/v1/auth/login
Body: { "username": "...", "password": "..." }

Response 200:
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400 }

GET /api/v1/auth/me    (requires Bearer token)
Response 200:
{ "id": "uuid", "username": "...", "email": "...", ... }
```

### 6.3 Deepfake Detection (Main Endpoint)
```
POST /api/v1/predict/audio    (requires Bearer token)
Content-Type: multipart/form-data
Body: file=<audio_file>

Response 200:
{
  "success": true,
  "label": "real",                   // or "fake"
  "confidence": 0.9997,
  "prob_real": 0.9997,
  "prob_fake": 0.0003,
  "winning_model": "mel_data3",
  "models_ran": 8,
  "per_model": {
    "mel_data3":  { "label": "real", "confidence": 0.9997, ... },
    "lfcc_data3": { "label": "real", "confidence": 0.9995, ... },
    ...  // all 8 models
  },
  "processing_time_ms": 1684.5,
  "prediction_id": "uuid",
  "filename": "test.wav"
}
```

**Error responses:**
| Status | Code | When |
|--------|------|------|
| 400 | `INVALID_FILE_TYPE` | Extension not `.wav`, `.mp3`, or `.flac` |
| 400 | `FILE_TOO_LARGE` | File exceeds 20 MB |
| 400 | `EMPTY_FILE` | Zero-byte upload |
| 400 | `INVALID_AUDIO` | File cannot be decoded as audio |
| 401 | `INVALID_TOKEN` | Missing or invalid JWT |
| 500 | `INFERENCE_ERROR` | ML pipeline failure |
| 503 | `MODELS_UNAVAILABLE` | No models loaded |

### 6.4 Prediction History
```
GET /api/v1/predictions/history?limit=20
GET /api/v1/predictions/{prediction_id}
```

---

## 7. Database Models

### Users (`apps/users/models.py`)
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key (not auto-increment) |
| `username` | String | From Django's AbstractUser |
| `email` | String | From Django's AbstractUser |
| `password` | String | Hashed by Django |
| `created_at` | DateTime | Auto-set on creation |

### UploadedAudio (`apps/uploads/models.py`)
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `user` | FK → User | Who uploaded (nullable) |
| `original_filename` | String | e.g. "test.wav" |
| `mime_type` | String | e.g. "audio/wav" |
| `file_size_bytes` | BigInt | File size in bytes |
| `uploaded_at` | DateTime | Auto-set |

### Prediction (`apps/predictions/models.py`)
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `user` | FK → User | Who requested (nullable) |
| `uploaded_audio` | FK → UploadedAudio | Link to file metadata |
| `final_label` | String | "real" or "fake" |
| `final_confidence` | Float | 0.0 – 1.0 |
| `winning_model` | String | e.g. "mel_data3" |
| `models_ran` | Int | How many models ran (usually 8) |
| `per_model` | JSON | Full 8-model probability breakdown |
| `processing_time_ms` | Float | Total pipeline time |
| `request_id` | String | Correlation ID |
| `created_at` | DateTime | Auto-set |

---

## 8. Authentication Flow

```
1. User sends POST /api/v1/auth/login with username + password
2. Django's authenticate() verifies credentials against the database
3. If valid → JWT signed with Django's SECRET_KEY (24-hour expiry)
4. Client stores the token and sends it as: Authorization: Bearer <token>
5. Every protected endpoint calls get_current_user():
   - Extracts Bearer token from header
   - Decodes JWT and verifies signature
   - Fetches User from database by user_id
   - Returns 401 if token is invalid/expired
   - Returns 403 if user account is inactive
```

---

## 9. Middleware

| Middleware | Header | Purpose |
|-----------|--------|---------|
| `RequestIDMiddleware` | `X-Request-ID` | Unique UUID per request for log correlation |
| `TimingMiddleware` | `X-Process-Time-Ms` | Total request processing time in ms |

Both values are stored on `request.state` and included in API responses.

---

## 10. Configuration System

Settings are split across environment-specific files:

| Environment | File | `APP_ENV` | Database | DEBUG |
|------------|------|-----------|----------|-------|
| Local Dev | `local.py` | `local` | SQLite | True |
| Staging/Docker | `staging.py` | `staging` | PostgreSQL | False |
| Production | `production.py` | `production` | PostgreSQL | False |

`config/settings/__init__.py` reads `APP_ENV` and imports the correct module automatically.

---

## 11. Docker Deployment

Three containers orchestrated by `docker-compose.yml`:

```
┌──────────────┐     ┌──────────────┐     ┌────────┐
│    Nginx     │────▶│   Backend    │────▶│  DB    │
│  (port 80)   │     │ (port 8000)  │     │ PG 15  │
│              │     │ Django+FastAPI│     │        │
│ Static files │     │ + 8 ML models│     │        │
└──────────────┘     └──────────────┘     └────────┘
```

**Startup sequence:**
1. PostgreSQL starts and passes health check
2. Backend container runs `collectstatic` → `migrate` → starts Gunicorn with 2 Uvicorn workers
3. All 8 ML models are loaded into memory
4. Nginx starts and begins proxying traffic

**Key commands:**
```bash
docker-compose up --build        # Build and start everything
docker-compose down              # Stop (data preserved)
docker-compose down -v           # Stop and DELETE all data
docker-compose logs -f backend   # View backend logs
```

---

## 12. Request Lifecycle (End-to-End)

```
1. Client → POST http://localhost/api/v1/predict/audio
                    │
2. Nginx receives → proxies to backend:8000
                    │
3. Gunicorn/Uvicorn worker picks up the request
                    │
4. RequestIDMiddleware → generates X-Request-ID
   TimingMiddleware   → starts timer
                    │
5. FastAPI route → get_current_user() validates JWT
                    │
6. _validate_file() → checks extension (.wav/.mp3/.flac) and size (≤20 MB)
                    │
7. audio_bytes = await file.read()
                    │
8. predict(audio_bytes):
   ├── librosa.load() → float32 mono @ 16 kHz
   ├── pad_or_truncate() → exactly 80,000 samples
   ├── extract_mel() → tensor (1, 128, T)
   ├── extract_lfcc() → tensor (1, T, 60)
   ├── Run 8 models → 8 × [P(real), P(fake)]
   └── aggregate() → most confident wins
                    │
9. create_prediction_record() → saves to PostgreSQL
                    │
10. Return JSON response ← Nginx ← Client
```

---

## 13. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **8 models, not 2** | Dataset was split into 4 batches; no single model saw all data |
| **Most-confident-wins** (not averaging) | Lets the most specialised model dominate |
| **CPU-only** | Keeps deployment simple; ResNet18 is small enough |
| **No silence trimming** | Training used pre-segmented clips — adding trim would cause mismatch |
| **spafe for LFCC** (not torchaudio) | Must match the exact library used during training |
| **tile-repeat padding** | Short audio is repeated (not zero-padded) to match training |
| **UUID primary keys** | No sequential IDs exposed — better for security |
| **sync_to_async for ORM** | Django ORM is synchronous; wrapped for FastAPI's async routes |
| **Models loaded at startup** | Never reload per-request — too expensive |

---

## 14. Dependencies

### Web/API
`django`, `fastapi`, `uvicorn`, `gunicorn`, `python-multipart`, `pydantic`, `PyJWT`

### Database
`psycopg2-binary`, `dj-database-url`

### ML/Audio
`torch`, `torchaudio`, `torchvision`, `numpy`, `librosa`, `spafe`, `soundfile`

### Testing
`pytest`, `pytest-django`, `httpx`

---

## 15. Running Locally (Without Docker)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
copy .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
uvicorn config.asgi:application --reload --port 8000

# Access:
#   http://localhost:8000/api/v1/health   → Health check
#   http://localhost:8000/api/v1/docs     → Swagger UI
#   http://localhost:8000/admin/          → Django admin
```

---

## 16. Running with Docker

```bash
# Build and start all containers
docker-compose up --build -d

# Create superuser inside container
docker exec -it deepfake_backend python manage.py createsuperuser

# Access:
#   http://localhost/api/v1/health   → Health check
#   http://localhost/api/v1/docs     → Swagger UI
#   http://localhost/admin/          → Django admin
```

---

## 17. Custom Exception Hierarchy

```
AudioLoadError          → Audio file cannot be decoded
FeatureExtractionError  → Mel or LFCC extraction failed
ModelLoadError          → .pth weight file cannot be loaded at startup
ModelNotLoadedError     → Inference attempted before models loaded
```

All are defined in `ml/utils/exceptions.py` and caught by the predict route to return appropriate HTTP error codes.

---

## 18. Frozen Training Parameters

These values are locked — changing ANY of them will break model accuracy:

| Parameter | Value | File |
|-----------|-------|------|
| Sample rate | 16,000 Hz | `audio_io.py` |
| Audio length | 5 seconds (80,000 samples) | `standardize.py` |
| Mel n_mels | 128 | `mel_features.py` |
| Mel hop_length | 512 | `mel_features.py` |
| Mel n_fft | 2048 | `mel_features.py` |
| LFCC num_ceps | 60 | `lfcc_features.py` |
| LFCC nfilts | 128 | `lfcc_features.py` |
| LFCC nfft | 2048 | `lfcc_features.py` |
| Label 0 | "real" | `constants.py` |
| Label 1 | "fake" | `constants.py` |
| Checkpoint key | `model_state_dict` | `model_registry.py` |
