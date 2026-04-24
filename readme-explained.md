# Deepfake Audio Detection Backend — Engineering Reference

> Distilled from `project-software-specification.md` · Django + FastAPI + PyTorch (CPU) · Ensemble Inference

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [Why This Stack Was Chosen](#2-why-this-stack-was-chosen)
3. [End-to-End Request Lifecycle](#3-end-to-end-request-lifecycle)
4. [Project Folder Structure](#4-project-folder-structure)
5. [ML Inference: The Core Engine](#5-ml-inference-the-core-engine)
6. [Preprocessing Pipeline — The Most Critical Section](#6-preprocessing-pipeline--the-most-critical-section)
7. [API Surface](#7-api-surface)
8. [Database Design](#8-database-design)
9. [Security Model](#9-security-model)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Observability](#11-observability)
12. [Testing Strategy](#12-testing-strategy)
13. [Known Risks & Mitigations](#13-known-risks--mitigations)
14. [Environment Variables Reference](#14-environment-variables-reference)
15. [Implementation Roadmap](#15-implementation-roadmap)
16. [Definition of Done (v1)](#16-definition-of-done-v1)

---

## 1. What This System Does

This backend detects whether a given audio clip is **real** (genuine human speech) or **fake** (synthetically generated / deepfake). It does so by:

1. Accepting an uploaded audio file over HTTP.
2. Running a deterministic preprocessing pipeline that normalises the audio to a fixed format.
3. Extracting **two independent feature representations** — Mel-Spectrogram and LFCC.
4. Running each feature through **4 independently trained ResNet18 models** (one per data batch) — 8 models in total.
5. Selecting the **most confident prediction** across all 8 model outputs (the model with the highest `max(softmax probability)` wins).
6. Returning a final `real` / `fake` label with a confidence score and full per-model breakdown.
7. Persisting every prediction to PostgreSQL for history, audit, and analytics.

The ML pipeline (audio decoding → feature extraction → PyTorch inference) **already exists**. The purpose of this backend is to wrap it in a production-grade, secure, maintainable, and frontend-ready service.

---

## 2. Why This Stack Was Chosen

The architecture deliberately splits responsibilities between two frameworks. This is an opinionated but sound decision.

### Django — The System Backbone

Django handles everything that is *operational*, *stateful*, and *admin-oriented*:

| Concern | Rationale |
|---|---|
| Authentication & Authorization | Django's auth system is battle-tested and integrates tightly with the ORM |
| Database ORM & Migrations | Schema evolution without raw SQL; Django Admin for free |
| Admin Panel | Inspect predictions, users, failures, and model versions without building a UI |
| Prediction History | Business logic belongs in Django services, not in the inference API |
| Audit Logs | User/system event tracking via Django models |

### FastAPI — The Inference Surface

FastAPI handles everything that is *API-first*, *schema-driven*, and *ML-serving-oriented*:

| Concern | Rationale |
|---|---|
| Typed Request/Response Schemas | Pydantic enforces contracts at the boundary, not inside the code |
| File Upload Endpoints | `python-multipart` + async file handling fits naturally |
| Auto-generated API Docs | `/docs` (Swagger) and `/redoc` come for free |
| ML Route Isolation | Inference routes are cleanly separated from business logic |

> **Rule of thumb**: Django owns the *platform*. FastAPI owns the *inference API surface*. They share the same PostgreSQL database and the same service layer underneath.

---

## 3. End-to-End Request Lifecycle

```
Client App
    │
    ▼
Nginx (reverse proxy, SSL termination, body size enforcement)
    │
    ▼
FastAPI (auth check, schema validation, file ingestion)
    │
    ▼
Preprocessing Service
    ├── Decode audio (torchaudio / soundfile)
    ├── Trim leading/trailing silence
    ├── Resample → 16 kHz
    ├── Convert to mono
    ├── Pad or truncate → exactly 5 seconds
    ├── Extract Mel-Spectrogram tensor
    └── Extract LFCC tensor
    │
    ▼
Model Service (8 models loaded once at startup, held in memory)
    ├── ResNet18 Mel  [data3] → P_mel_3(real),  P_mel_3(fake)
    ├── ResNet18 Mel  [data5] → P_mel_5(real),  P_mel_5(fake)
    ├── ResNet18 Mel  [data6] → P_mel_6(real),  P_mel_6(fake)
    ├── ResNet18 Mel  [data8] → P_mel_8(real),  P_mel_8(fake)
    ├── ResNet18 LFCC [data3] → P_lfcc_3(real), P_lfcc_3(fake)
    ├── ResNet18 LFCC [data5] → P_lfcc_5(real), P_lfcc_5(fake)
    ├── ResNet18 LFCC [data6] → P_lfcc_6(real), P_lfcc_6(fake)
    └── ResNet18 LFCC [data8] → P_lfcc_8(real), P_lfcc_8(fake)
    │
    ▼
Aggregation: Most-Confident-Wins
    For each model i:  confidence_i = max(P_i(real), P_i(fake))
    winner = argmax(confidence_i across all 8 models)
    label      = label of winning model
    confidence = confidence of winning model
    │
    ▼
PostgreSQL (persist upload metadata + full per-model prediction results)
    │
    ▼
JSON Response → Client
```

The full timing breakdown (preprocessing ms, inference ms, total ms) is included in every response.

---

## 4. Project Folder Structure

```
deepfake-audio-backend/
├── config/                     # Django project config
│   └── settings/
│       ├── base.py             # Shared settings
│       ├── local.py            # Dev overrides
│       ├── staging.py          # Staging overrides
│       └── production.py       # Production overrides
│
├── apps/                       # Django apps (business domain)
│   ├── users/                  # Custom user model, auth services
│   ├── predictions/            # Prediction model, history, services
│   ├── uploads/                # Upload model, validators, storage
│   └── audit_logs/             # Audit event model
│
├── api/                        # FastAPI application
│   ├── fastapi_app.py          # FastAPI app factory
│   ├── routes/
│   │   ├── predict.py          # POST /api/v1/predict/audio
│   │   ├── health.py           # GET  /api/v1/health
│   │   └── auth.py             # Login / logout / me
│   └── schemas/                # Pydantic request/response models
│
├── ml/                         # Isolated ML code — never scatter this
│   ├── models/
│   │   ├── resnet18_mel.py     # Model architecture definition
│   │   ├── resnet18_lfcc.py    # Model architecture definition
│   │   ├── loader.py           # Weight loading logic
│   │   └── registry.py        # Model version registry
│   ├── weights/
│   │   ├── resnet18_mel.pth    # Trained weights (CPU)
│   │   └── resnet18_lfcc.pth   # Trained weights (CPU)
│   ├── preprocessing/
│   │   ├── audio_io.py         # Decode / load audio
│   │   ├── silence_trim.py     # Silence removal (must match training)
│   │   ├── standardize.py      # Resample + mono + 5s normalisation
│   │   ├── mel_features.py     # Mel-spectrogram extraction
│   │   ├── lfcc_features.py    # LFCC extraction
│   │   └── pipeline.py         # Orchestrates full preprocessing
│   └── inference/
│       ├── predictor.py        # Main prediction service
│       ├── ensemble.py         # Probability averaging logic
│       ├── postprocess.py      # Label/confidence extraction
│       └── cpu_runner.py       # torch.no_grad() inference wrapper
│
├── tests/
│   ├── unit/                   # Validators, preprocessing, ensemble
│   ├── integration/            # Upload + predict + DB full flow
│   ├── contract/               # Response shape stability
│   ├── regression/             # Known audio → expected labels
│   └── load/                   # Concurrent upload benchmarks
│
├── media/uploads/              # Temporary request-local audio storage
├── logs/                       # Structured JSON log output
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

> **Critical rule**: All ML logic lives under `ml/`. Routes are thin orchestrators. Never write preprocessing logic directly inside a FastAPI route handler.

---

## 5. ML Inference: The Core Engine

### Eight-Model Inference System

The dataset was split into **4 non-overlapping batches** during training. No single model saw the full dataset. To compensate for this, **all 8 models run on every request** — the backend effectively gives all models a vote and lets the most confident one decide.

```
Batch  | Mel Model                    | LFCC Model
-------|------------------------------|------------------------------
data3  | best_resnet18_mel_3.pth      | best_resnet18_lfcc_3.pth
data5  | best_resnet18_mel_5.pth      | best_resnet18_lfcc_5.pth
data6  | best_resnet18_mel_6.pth      | best_resnet18_lfcc_6.pth
data8  | best_resnet18_mel_8.pth      | best_resnet18_lfcc_8.pth
```

**Total models loaded at startup: 8**

### Aggregation: Most-Confident-Wins

Each model produces a softmax probability vector `[P(real), P(fake)]`. The final prediction is determined by which model is *most certain*:

```
For each model i in {mel_3, mel_5, mel_6, mel_8, lfcc_3, lfcc_5, lfcc_6, lfcc_8}:
    confidence_i = max(P_i(real), P_i(fake))
    label_i      = "real" if P_i(real) > P_i(fake) else "fake"

winner     = argmax(confidence_i)
final_label      = label_winner
final_confidence = confidence_winner
```

The response includes **all 8 per-model outputs** so the frontend (and debugging tools) can see the full picture, not just the winner.

### Model Loading Rules

```python
# Done ONCE at application startup for all 8 models
BATCHES = ["data3", "data5", "data6", "data8"]

for batch in BATCHES:
    for feature in ["mel", "lfcc"]:
        path = f"ml/weights/{batch}/models/best_resnet18_{feature}_{batch[-1]}.pth"
        model = build_resnet18_architecture()
        state = torch.load(path, map_location=torch.device("cpu"))
        model.load_state_dict(state)
        model.eval()
        model_registry[(batch, feature)] = model
```

- Use `map_location="cpu"` unconditionally for now.
- Call `model.eval()` immediately after loading.
- Wrap all inference calls in `torch.no_grad()`.
- **Never instantiate or load weights inside a request handler** — this will collapse performance under any real load.
- All 8 models are registered in a dictionary keyed by `(batch, feature_type)` and held in process memory.
- Label index contract: `index 0 → real`, `index 1 → fake`. Assert this at startup with known test inputs.

---

## 6. Preprocessing Pipeline — The Most Critical Section

> **The #1 production failure mode is a training/serving preprocessing mismatch.** If even one parameter differs between what the model was trained on and what the backend feeds it, accuracy silently degrades without any obvious error.

Every step below must exactly replicate the training-time logic:

| Step | What Happens | Key Concern |
|---|---|---|
| **Upload Validation** | Check file exists, size > 0, allowed MIME type/extension, decodable | Reject early, fail fast |
| **Decode Audio** | Load waveform tensor + detected sample rate | Use same library as training |
| **Trim Silence** | Remove leading/trailing silence | `threshold`, `frame_length`, `hop_length` must match training exactly |
| **Resample** | Normalise to 16 kHz | All audio must pass through regardless of source SR |
| **Mono Conversion** | Collapse multi-channel to single channel | Use same method (averaging vs. single-channel select) as training |
| **5-Second Normalisation** | Pad if shorter, truncate if longer | Must be deterministic; match training pad/truncate strategy |
| **Mel-Spectrogram** | Compute with exact `n_fft`, `hop_length`, `win_length`, `n_mels`, `f_min`, `f_max`, normalisation | All params must be frozen from training config |
| **LFCC** | Compute with exact frame size, hop length, number of coefficients, delta handling | Same freeze requirement |
| **Tensor Shaping** | Add batch dim, channel dim, correct dtype, image-like format for ResNet | Shape mismatch = silent wrong predictions |

### Preprocessing Failure Modes

Reject the request (return 422) if:
- Audio cannot be decoded
- Trimmed audio becomes empty (completely silent file)
- Feature extraction fails
- Tensor shape after extraction is invalid
- Audio is too short after trimming to be normalised to 5 seconds

---

## 7. API Surface

All endpoints are versioned under `/api/v1/`.

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/predict/audio` | Required | Upload audio file, get prediction |
| `GET` | `/api/v1/predictions/{id}` | Required | Fetch a single prediction |
| `GET` | `/api/v1/predictions/history` | Required | List authenticated user's history |
| `POST` | `/api/v1/auth/login` | None | Obtain JWT tokens |
| `POST` | `/api/v1/auth/logout` | Required | Invalidate session |
| `GET` | `/api/v1/auth/me` | Required | Current user info |
| `GET` | `/api/v1/health` | None | Model + DB readiness |
| `GET` | `/api/v1/version` | None | Service version info |
| `GET` | `/admin/` | Admin | Django admin panel |

### Predict Request

```http
POST /api/v1/predict/audio
Content-Type: multipart/form-data
Authorization: Bearer <token>

audio_file: <file>       # required
request_id: <string>     # optional, client correlation ID
```

### Success Response Shape

```json
{
  "success": true,
  "prediction_id": "0c1fb8bb-8d8e-4d7c-8674-83a0f8c1d441",
  "label": "fake",
  "confidence": 0.9274,
  "probabilities": { "real": 0.0726, "fake": 0.9274 },
  "model_outputs": {
    "mel":  { "real": 0.0811, "fake": 0.9189 },
    "lfcc": { "real": 0.0641, "fake": 0.9359 }
  },
  "ensemble": "average_probability",
  "audio": {
    "original_filename": "sample.wav",
    "duration_seconds_input": 7.2,
    "duration_seconds_used": 5.0,
    "sample_rate_used": 16000,
    "channels_used": 1
  },
  "timing": { "preprocessing_ms": 142, "inference_ms": 88, "total_ms": 251 },
  "model_version": { "mel": "resnet18_mel_v1", "lfcc": "resnet18_lfcc_v1" },
  "request_id": "client-123"
}
```

### Error Response Shape (consistent for all errors)

```json
{
  "success": false,
  "error": {
    "code": "INVALID_AUDIO_FORMAT",
    "message": "Only wav, mp3, and flac files are supported.",
    "details": { "received_content_type": "application/octet-stream" }
  },
  "request_id": "client-123"
}
```

> **Stability contract**: JSON keys must not change between releases. Frontend integrations depend on them. Use contract tests to enforce this.

---

## 8. Database Design

**PostgreSQL** is the only supported production database. Use SQLite only for quick local bootstrapping.

### Core Tables

#### `users`
Standard Django user model or custom. Fields: `id (UUID)`, `email`, `password_hash`, `is_active`, `is_staff`, `created_at`, `updated_at`.

#### `uploaded_audio`
Stores file metadata — not the raw audio bytes (unless explicitly needed).
Fields: `id`, `user_id`, `original_filename`, `stored_path`, `mime_type`, `file_size_bytes`, `input_duration_seconds`, `sample_rate_detected`, `uploaded_at`.

#### `prediction`
The main result table. Stores both final ensemble output and per-model probabilities (critical for debugging and analysis).
Fields: `id`, `user_id`, `uploaded_audio_id`, `final_label`, `final_confidence`, `final_prob_real`, `final_prob_fake`, `mel_prob_real`, `mel_prob_fake`, `lfcc_prob_real`, `lfcc_prob_fake`, `ensemble_method`, `model_version_mel`, `model_version_lfcc`, `preprocessing_ms`, `inference_ms`, `total_ms`, `request_id`, `created_at`.

#### `model_registry`
Tracks which model versions are active. Fields: `id`, `model_name`, `model_type`, `version`, `weight_path`, `label_map`, `is_active`, `created_at`.

#### `audit_log`
Records important user/system events for compliance and debugging.
Fields: `id`, `user_id`, `action`, `endpoint`, `status_code`, `ip_address`, `metadata_json`, `created_at`.

> **Design notes**: Always use UUIDs for external-facing IDs. Store **all 8 per-model probabilities** — they are invaluable for debugging, model comparison, and understanding which batch generalises best to unseen audio. Keep `uploaded_audio` and `prediction` separate; don't conflate file metadata with inference outputs.

---

## 9. Security Model

Security is not an afterthought — it is designed in from day one.

| Area | Policy |
|---|---|
| **Authentication** | JWT access + refresh tokens. Session auth only if same-domain frontend. |
| **Authorization** | Users access only their own prediction records. Admin routes protected by `is_staff`. |
| **CORS** | Explicit allowed origins only. Never `*` in production when auth headers are involved. |
| **File Validation** | Enforce allowed extensions (`.wav`, `.mp3`, optionally `.flac`), MIME type check, max 20 MB, single file per request. Decode check before processing. |
| **Filenames** | Never trust the client-provided filename. Generate UUID-based storage names. |
| **Rate Limiting** | Per-user and per-IP limits. Prevents abuse and CPU exhaustion (both models run on every request). |
| **Secrets** | All sensitive values (SECRET_KEY, DB credentials, JWT secrets, model paths) must come from environment variables — never hardcoded. |
| **Logging** | Never log tokens, passwords, sensitive user data, or raw file contents. Log only safe metadata. |

---

## 10. Deployment Architecture

### Environments

| Environment | Stack |
|---|---|
| **Local Dev** | Python venv + SQLite or local PostgreSQL + Uvicorn directly |
| **Staging** | Docker Compose + PostgreSQL + Nginx + Gunicorn/Uvicorn + test model weights |
| **Production** | Docker + Nginx (SSL, body limits, security headers) + Gunicorn managing Uvicorn workers + PostgreSQL + optional Redis |

### Process Architecture

Two options for deploying Django + FastAPI together:
- **Option A** (recommended initially): Single ASGI app that mounts both Django (via `django-asgi`) and FastAPI under Nginx routing.
- **Option B** (later): Two separate processes behind Nginx — Django on one upstream, FastAPI on another.

Start with Option A. Split only when the operational complexity of a single container justifies it.

### Nginx Responsibilities
- Reverse proxy to app container
- SSL/TLS termination
- `client_max_body_size` enforcement (e.g., 25 MB)
- Request buffering
- Security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.)

### Worker Tuning (Gunicorn + Uvicorn)

```
gunicorn -k uvicorn.workers.UvicornWorker --workers N app:asgi_app
```

Tune `N` based on: CPU core count, average request latency, memory footprint per worker. Benchmark before setting a production value — both models are held in memory per worker.

---

## 11. Observability

### Structured Logging (JSON)

Every request log entry should include:
```
request_id | endpoint | user_id | file metadata | preprocessing_ms | inference_ms | total_ms | model_version | outcome | error_code
```

### Metrics to Track

- Request count, success rate, failure rate
- p50 / p95 / p99 latency
- Preprocessing time, inference time, DB query time separately
- CPU usage, memory usage per worker
- Model load status at startup

### Health Check

```
GET /api/v1/health
```

Returns model load status (`mel_loaded`, `lfcc_loaded`) and DB connectivity. Must return `200` only when both models are loaded and the database is reachable. Used by load balancers and orchestrators for readiness probes.

---

## 12. Testing Strategy

Testing covers both software correctness **and** ML serving correctness.

| Test Type | What It Covers |
|---|---|
| **Unit** | Audio validators, each preprocessing function, ensemble averaging math, label mapping, error formatting, model loader isolation |
| **Integration** | Full upload → preprocess → infer → persist → respond flow; auth-protected endpoints; invalid/corrupt audio; missing model files |
| **Contract** | Response keys, status codes, and error shape are stable across code changes (critical for frontend integration) |
| **Model Regression** | Locked reference audio samples with known expected labels — run on every deployment to detect silent accuracy drift |
| **Load** | Concurrent upload throughput, p95 latency under realistic concurrency, CPU saturation behaviour, error rate under load |

---

## 13. Known Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Preprocessing mismatch (train vs. serve)** | Silent accuracy drop — hardest to debug | Centralise all pipeline config; freeze it; run regression tests with known samples on every deploy |
| **Wrong label order** | `real`/`fake` probabilities swapped — catastrophic but silent | Explicitly define and assert label map at startup; test known examples |
| **`.pth` loading incompatibility** | Startup crash or wrong weights silently loaded | Version model architecture code alongside weights; use state-dict loading; document exact architecture used during training |
| **CPU saturation** | Latency spikes, timeouts, queued requests | Benchmark properly; tune worker count; rate-limit aggressively; add async queue (Celery/Redis) when traffic warrants |
| **Invalid/corrupt audio input** | Decode failures, crashes, resource leaks | Strict file validators; temp-storage-only processing; controlled exception handling with structured error responses |
| **Silent feature extraction failure** | Malformed tensor causes wrong prediction with no error | Assert tensor shapes after extraction; log feature dimensions; fail fast on any mismatch |

---

## 14. Environment Variables Reference

```bash
# Application
APP_ENV=local                          # local | staging | production
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/deepfake_audio

# Optional (recommended for async later)
REDIS_URL=redis://localhost:6379/0

# File Storage
MEDIA_ROOT=./media
MAX_UPLOAD_SIZE_MB=20

# ML Models
MODEL_MEL_PATH=./ml/weights/resnet18_mel.pth
MODEL_LFCC_PATH=./ml/weights/resnet18_lfcc.pth
MODEL_LABELS=real,fake            # Index order — must match training

# Audio Processing
STANDARD_SAMPLE_RATE=16000
AUDIO_FIXED_SECONDS=5

# Auth
ACCESS_TOKEN_SECRET=change-this-too
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Logging
LOG_LEVEL=INFO
```

---

## 15. Implementation Roadmap

| Phase | What Gets Built |
|---|---|
| **Phase 1 — Skeleton** | Django project + FastAPI app, PostgreSQL, settings split (base/local/staging/prod), structured logging, env loading |
| **Phase 2 — ML Integration** | Port preprocessing into `ml/preprocessing/`, port model architecture into `ml/models/`, implement model loader + CPU inference service + ensemble logic, validate output parity against existing local scripts |
| **Phase 3 — API Layer** | `POST /api/v1/predict/audio`, `GET /api/v1/health`, Pydantic request/response schemas, validation + error handling, request IDs + structured logging |
| **Phase 4 — Persistence** | Django ORM models for `uploaded_audio`, `prediction`, `model_registry`, `audit_log`; admin registration; prediction history endpoint |
| **Phase 5 — Security & Frontend Readiness** | JWT auth, CORS config, rate limiting, file size/type restrictions, stable API contracts |
| **Phase 6 — Deployment Hardening** | Dockerfile + Docker Compose, Nginx config, Gunicorn/Uvicorn tuning, staging deploy, load tests, health check validation |
| **Phase 7 — Production Launch** | Production environment deploy, monitoring enabled, backups, regression suite run, model versions frozen, API contract published |

---

## 16. Definition of Done (v1)

The backend is **production-ready** when all of the following are true:

### Functional
- [ ] Audio upload endpoint works with supported file types (`.wav`, `.mp3`, `.flac`)
- [ ] Both models load successfully at startup
- [ ] Both models run for every valid request
- [ ] Final prediction is computed by averaging both model probabilities
- [ ] Labels are correctly returned as `real` or `fake`
- [ ] Prediction results are stored in the database
- [ ] Authenticated users can retrieve their prediction history
- [ ] Admin can inspect all records via Django admin

### Technical
- [ ] Exact training-time preprocessing is reproduced in serving (verified by regression tests)
- [ ] CPU inference path is benchmarked (p95 latency documented)
- [ ] Health endpoint accurately reports model and DB readiness
- [ ] Structured JSON logging is enabled
- [ ] Error handling is standardised (consistent error contract shape)
- [ ] CORS is configured for the target frontend origin(s)
- [ ] Environment-based settings are working across all environments
- [ ] Docker deployment works in staging

### Security
- [ ] File size/type validation is enforced
- [ ] Authentication is required for all protected endpoints
- [ ] Rate limiting is configured (per-user and per-IP)
- [ ] All secrets are environment-variable-based (none hardcoded)
- [ ] Uploaded filenames are sanitised / replaced with UUID-generated names

### Quality
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Contract tests pass (response shape stability enforced)
- [ ] Model regression tests pass (known audio → expected labels)
- [ ] Load test baseline is documented

---

## Quick Reference: Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Django + FastAPI (not one or the other) | Django for platform concerns (auth, ORM, admin); FastAPI for inference API surface. Clean separation avoids conflating business logic with ML serving. |
| CPU-only for v1 | Simplifies deployment significantly. Architecture abstracts device selection so GPU migration doesn't require API changes. |
| **8 models (4 batches × 2 features) on every request** | Dataset was split into 4 disjoint batches during training — no single model saw everything. Running all 8 ensures the most-informed model always gets to answer. |
| **Most-confident-wins aggregation** | Probability averaging would dilute a highly confident model with a less certain one from a different data domain. Picking the max-confidence model is more faithful to what each model actually knows. |
| Preprocessing code isolated in `ml/` | The single most important design decision. A scattered preprocessing function that drifts from the training pipeline destroys model accuracy silently. |
| Models loaded once at startup | Per-request model loading would make inference ~10–100× slower. Hold all 8 in memory; expose via a service registry. |
| Synchronous inference for v1 | Single-file uploads with bounded audio length are fast enough synchronously even with 8 models. Async job queue (Celery + Redis) is the v2 path when batch or long-audio use cases emerge. |
| PostgreSQL as primary store | Store per-model probabilities for all 8 models, not just the final label — essential for debugging, model comparison, and future analytics. |
