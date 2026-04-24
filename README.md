# Deepfake Audio Detection Backend

**Production-Oriented README for Django + FastAPI + PyTorch (CPU-Only) Ensemble
Inference**

## 1. Overview

This project provides a production-oriented backend for **Deepfake Audio Detection** using:

```
Django for core backend responsibilities
FastAPI for inference-focused API endpoints
PyTorch for model loading and inference
CPU-only deployment for the current release
Two ResNet18 models :
resnet18_mel.pth
resnet18_lfcc.pth
```
The system performs inference using **both models for every request** , then **averages their
prediction probabilities** to generate a final classification:

```
real
fake
```
The ML pipeline already exists and includes:

```
audio decoding
mono conversion
fixed sample rate normalization
trimming silence from beginning and end
fixed audio length of 5 seconds
feature extraction:
Mel-spectrogram for one model
LFCC for the other model
PyTorch-based inference
```
This README describes how to build a robust backend around that pipeline in a way that is
maintainable, secure, scalable, and ready for future frontend integration.

## 2. Goals

### Primary Goals

```
Expose a clean, versioned API for deepfake audio detection
Load and serve two ResNet18 models on CPU
Apply the exact training-time preprocessing in backend inference
Average the outputs of both models for final prediction
Store prediction history and request metadata
Support future frontend integration cleanly
Provide authentication, validation, logging, and admin capabilities
Be production-friendly from the beginning
```
### Secondary Goals

```
Keep the architecture extensible for:
```

```
batch inference
async processing
GPU migration
model versioning
cloud storage
containerized deployment
```
## 3. Non-Goals

The initial version does **not** aim to include:

```
real-time streaming inference
WebSocket audio streaming
automatic model retraining
MLOps pipeline orchestration
multi-tenant billing/subscriptions
GPU optimization in the first release
distributed inference cluster
```
These can be added later, but should not complicate the first production-ready backend.

## 4. Why Django + FastAPI

This architecture is intentionally opinionated:

### Django is used for

```
authentication and authorization
admin panel
database models and migrations
user management
prediction history
operational controls
stable backend project structure
```
### FastAPI is used for

```
inference-centric API design
typed request/response schemas
file upload endpoints
low-friction async-compatible API layer
auto-generated API documentation
cleaner separation of ML-serving routes
```
### Why not only Django?

You could build the entire backend using Django or Django REST Framework. But in this use
case:

```
inference endpoints are specialized
file upload + schema validation is central
future frontend/API consumers benefit from a dedicated API-first layer
model-serving logic is easier to isolate in FastAPI
```
### Why not only FastAPI?

You could. But Django provides strong built-in value for:


```
admin
auth
ORM
migrations
internal operations
user/role management
```
### Recommended Position

Use:

```
Django as the system backbone
FastAPI as the inference API surface
Shared DB and shared services underneath
```
This gives a clean separation between **application platform concerns** and **ML inference
concerns**.

## 5. End-to-End Architecture

At a high level:

1. Client uploads an audio file to the FastAPI inference endpoint
2. Request is authenticated and validated
3. Audio is decoded and normalized
4. Silence is trimmed
5. Audio is resampled and converted to mono if required
6. Audio is padded/truncated to exactly 5 seconds
7. Two feature pipelines run:
    Mel-spectrogram
    LFCC
8. Each feature is passed to its respective ResNet18 model
9. Both model probabilities are averaged
10. Final label and confidence are computed
11. Request and prediction metadata are saved to PostgreSQL
12. Response is returned as JSON
13. Logs/metrics are recorded for observability

## 6. High-Level Architecture Diagram

flowchart LR FE[Frontend / Client App] --> NGINX[Nginx Reverse Proxy] NGINX -->
API[FastAPI Inference API] NGINX --> DJ[Django Core / Admin / Auth] API -->
PRE[Preprocessing Service] PRE --> MEL[Mel Feature Extractor] PRE --> LFCC[LFCC Feature
Extractor] MEL --> M1[ResNet18 Mel Model] LFCC --> M2[ResNet18 LFCC Model] M1 -->
ENS[Ensemble Averaging Service] M2 --> ENS ENS --> DB[(PostgreSQL)] DJ --> DB API -->
LOGS[Structured Logs / Metrics] DJ --> LOGS DJ --> ADMIN[Django Admin]

## 7. System Requirements

## 7.1 Runtime Assumptions

```
Current serving target is CPU-only
Architecture should remain extensible for future GPU support
Models are already trained and available locally
Inference should reproduce training-time preprocessing exactly
```

## 7.2 Operating System

Recommended:

```
Ubuntu 22.04 LTS or similar Linux distribution
```
Supported for local development:

```
Windows 10/1 1
macOS
Linux
```
Production recommendation: **Linux**

## 7.3 Python Version

Recommended:

```
Python 3.10 or Python 3.1 1
```
Avoid frequent version changes once the environment is validated against PyTorch and audio
libraries.

## 7.4 Core Software Stack

```
Python
Django
FastAPI
Uvicorn
Gunicorn
PyTorch
Torchaudio
NumPy
PostgreSQL
Redis (optional initially, recommended later)
Celery or RQ (optional for async jobs)
Nginx
Docker / Docker Compose
```
## 7.5 Required Python Packages

Minimum practical package categories:

```
Web/API:
django
fastapi
uvicorn
gunicorn
python-multipart
pydantic
ML/Audio:
torch
torchaudio
numpy
optionally scipy
optionally librosa
optionally soundfile
Database:
psycopg2-binary
```

```
Config:
python-dotenv
Background jobs:
celery
redis
Monitoring/logging:
structlog or standard logging setup
Testing:
pytest
pytest-django
httpx
```
## 7.6 Hardware Assumptions

### Development

```
CPU: 4+ cores
RAM: 8–16 GB
SSD recommended
```
### Production, Small to Medium Load

```
CPU: 8+ cores
RAM: 16–32 GB
SSD
No GPU required initially
```
Because both models run on every request, CPU capacity planning matters.

## 8. ML Asset Requirement Checklist

Before backend implementation starts, the following assets must be finalized and versioned.

## 8.1 Required Model Assets

```
resnet18_mel.pth
resnet18_lfcc.pth
exact ResNet18 architecture code used during training
custom wrappers or heads if any
model configuration per feature pipeline
```
## 8.2 Required Feature Pipeline Assets

```
fixed sample rate value
silence trimming rules
exact 5-second alignment behavior
padding and truncation strategy
mel-spectrogram parameters
LFCC parameters
normalization rules
tensor shapes expected by each model
channel arrangement expected by each model
```
## 8.3 Required Prediction Assets

```
label order
```

```
index 0 -> real
index 1 -> fake
softmax handling
threshold policy
confidence selection policy
ensemble averaging rule
```
## 8.4 Required Validation Assets

```
sample valid audio files
sample invalid/corrupt files
known-good test cases for both classes
regression benchmark outputs for production validation
```
## 9. Recommended Production Folder Structure

deepfake-audio-backend/
├── README.md
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
│
├── config/
│ ├── __init__.py
│ ├── asgi.py
│ ├── wsgi.py
│ ├── urls.py
│ ├── settings/
│ │ ├── __init__.py
│ │ ├── base.py
│ │ ├── local.py
│ │ ├── staging.py
│ │ └── production.py
│
├── apps/
│ ├── users/
│ │ ├── models.py
│ │ ├── admin.py
│ │ ├── services.py
│ │ └── migrations/
│ │
│ ├── predictions/
│ │ ├── models.py
│ │ ├── admin.py
│ │ ├── services.py
│ │ ├── selectors.py
│ │ └── migrations/
│ │
│ ├── uploads/
│ │ ├── models.py
│ │ ├── validators.py
│ │ ├── storage.py
│ │ └── migrations/
│ │
│ ├── audit_logs/
│ │ ├── models.py
│ │ ├── admin.py
│ │ └── migrations/


│
├── api/
│ ├── fastapi_app.py
│ ├── dependencies.py
│ ├── middleware.py
│ ├── routes/
│ │ ├── health.py
│ │ ├── predict.py
│ │ ├── auth.py
│ │ └── system.py
│ ├── schemas/
│ │ ├── predict.py
│ │ ├── common.py
│ │ └── auth.py
│
├── ml/
│ ├── models/
│ │ ├── resnet18_mel.py
│ │ ├── resnet18_lfcc.py
│ │ ├── loader.py
│ │ └── registry.py
│ │
│ ├── weights/
│ │ ├── resnet18_mel.pth
│ │ └── resnet18_lfcc.pth
│ │
│ ├── preprocessing/
│ │ ├── audio_io.py
│ │ ├── silence_trim.py
│ │ ├── standardize.py
│ │ ├── mel_features.py
│ │ ├── lfcc_features.py
│ │ └── pipeline.py
│ │
│ ├── inference/
│ │ ├── predictor.py
│ │ ├── ensemble.py
│ │ ├── postprocess.py
│ │ └── cpu_runner.py
│ │
│ └── utils/
│ ├── constants.py
│ └── exceptions.py
│
├── media/
│ ├── uploads/
│ └── failed/
│
├── logs/
│
└── tests/
├── unit/
├── integration/
├── contract/
├── regression/
└── load/

## 10. Component-by-Component Architecture

## 10.1 Django Core

Responsibilities:


```
user management
authentication and authorization
database ORM
migration system
admin panel
prediction history management
audit logs
environment-specific settings
long-term business logic
```
Keep Django as the **system backbone**.

## 10.2 FastAPI Inference App

Responsibilities:

```
request validation
audio upload handling
inference route definitions
response schemas
API-first surface for frontend
health/status endpoints
```
Keep FastAPI focused on **stateless inference orchestration** , not business-heavy persistence logic.

## 10.3 Model Service

Responsibilities:

```
load both .pth models on startup
keep them in memory
ensure CPU map location
switch to evaluation mode
expose prediction methods to the API layer
```
This service must avoid loading model weights on every request.

## 10.4 Preprocessing Service

Responsibilities:

```
audio file ingestion
decode audio
validate audio integrity
trim silence
resample
mono conversion
fixed 5-second standardization
generate mel-spectrogram tensor
generate LFCC tensor
shape tensors for model input
```
This service must replicate the **training pipeline exactly**.

## 10.5 Persistence Layer

Responsibilities:

```
store uploaded file metadata
store prediction metadata
```

```
store probabilities and final result
enable history retrieval
support admin review and analytics
```
Recommended DB: **PostgreSQL**

## 10.6 Logging

Responsibilities:

```
request logs
validation failures
inference errors
processing latency
model loading status
admin/audit events
```
Use structured JSON logs in production.

## 10.7 Admin

Use Django Admin for:

```
user management
viewing uploaded audio metadata
viewing predictions
viewing failures
model version visibility
audit monitoring
```
## 10.8 Monitoring

At minimum:

```
health checks
request counts
latency
failure rate
model load status
CPU usage
DB connectivity
```
## 11. Ensemble Logic: Two-Model Averaging

Both models are executed for every request:

```
Model A: Mel-based ResNet
Model B: LFCC-based ResNet
```
Each model produces logits or probabilities for two classes:

```
real
fake
```
## 11.1 Mathematical Form

Let:


```
P_mel(real) and P_mel(fake) be probabilities from Mel model
P_lfcc(real) and P_lfcc(fake) be probabilities from LFCC model
```
The final ensemble probabilities are:

P_final(real) = (P_mel(real) + P_lfcc(real)) / 2
P_final(fake) = (P_mel(fake) + P_lfcc(fake)) / 2

Final label:

label = argmax(P_final(real), P_final(fake))

Confidence:

confidence = max(P_final(real), P_final(fake))

## 11.2 Operational Form

1. Run preprocessing once on uploaded waveform
2. Generate Mel tensor
3. Generate LFCC tensor
4. Run Mel model inference
5. Run LFCC model inference
6. Convert outputs to probabilities
7. Average probabilities element-wise
8. Select max probability as final class
9. Return:
    final label
    confidence
    per-model outputs
    final averaged probabilities

## 11.3 Why Probability Averaging?

Probability averaging is a practical first-choice ensemble method because:

```
it is simple
it is explainable
it is deterministic
it works well when both models are already individually strong
it preserves visibility into each model’s contribution
```
## 12. Model Inference Pipeline Diagram

flowchart TD A[Uploaded Audio File] --> B[Decode Audio] B --> C[Trim Start/End Silence] C --
> D[Resample to Standard Sample Rate] D --> E[Convert to Mono] E --> F[Pad/Truncate to 5
Seconds] F --> G1[Generate Mel-Spectrogram] F --> G2[Generate LFCC] G1 --> H1[Tensor
Shape for Mel ResNet18] G2 --> H2[Tensor Shape for LFCC ResNet18] H1 -->
I1[resnet18_mel.pth] H2 --> I2[resnet18_lfcc.pth] I1 --> J1[Softmax Probabilities] I2 -->
J2[Softmax Probabilities] J1 --> K[Average Class Probabilities] J2 --> K K --> L[Final Label +
Confidence] L --> M[Persist Result + Return JSON]

## 13. Preprocessing Pipeline

This is one of the most critical parts of the backend. The production system must use the **same
logic as training**.

## 13.1 Upload Validation


Validate immediately:

```
file exists
file size > 0
content type allowed
extension allowed
request is multipart/form-data
decodeable as audio
```
Recommended allowed formats:

```
.wav
.mp
optionally .flac
```
## 13.2 Decode Audio

Use the same audio loading approach as training/inference code.

Output after decode:

```
waveform tensor/array
detected sample rate
```
## 13.3 Trim Silence

Trim silence from:

```
beginning
end
```
This step must exactly match the training rule, including:

```
threshold
frame length
hop length
silence detection behavior
```
If there is a mismatch here, production accuracy can degrade.

## 13.4 Resample

Resample to the standard training-time sample rate.

Example:

input sample rate -> target sample rate

All requests must pass through the same standardization.

## 13.5 Mono Conversion

Convert to mono if the source has multiple channels.

Use the same method used in training:

```
channel averaging
selecting one channel
or custom rule
```
Do not change this behavior between training and serving.


## 13.6 Fixed 5-Second Normalization

All inputs must become exactly **5 seconds**.

If shorter:

```
pad using the training-time strategy
```
If longer:

```
truncate using the training-time strategy
```
This must be deterministic.

## 13.7 Feature Extraction

### Mel-Spectrogram Path

Generate Mel features using the exact configuration used in training.

Typical parameters that must match:

```
sample rate
n_fft
hop_length
win_length
n_mels
f_min
f_max
log scaling
normalization
```
### LFCC Path

Generate LFCC features using the exact same settings used in training.

Typical required matching parameters:

```
sample rate
frame size
hop length
number of coefficients
normalization
delta handling if used
```
## 13.8 Tensor Shaping

Each model must receive tensors in the exact shape expected by the trained architecture.

Typical concerns:

```
batch dimension
channel dimension
dtype
normalization
image-like format for ResNet input
expected spatial resolution
```
## 13.9 Preprocessing Failure Modes


Reject safely if:

```
audio cannot be decoded
trimmed audio becomes empty
feature extraction fails
tensor shape is invalid
audio is too short after trimming and cannot be normalized properly
unsupported format is uploaded
```
## 14. PyTorch Model Loading Strategy

The backend should follow a strict loading strategy.

## 14.1 Principles

```
load models once at startup
load using state_dict if the .pth files are state dictionaries
instantiate exact model architecture before loading weights
use map_location="cpu"
call model.eval()
use torch.no_grad() during inference
```
## 14.2 Recommended Flow

model = build_model_architecture()
state = torch.load(model_path, map_location=torch.device("cpu"))
model.load_state_dict(state)
model.eval()

## 14.3 Why Startup Loading Matters

Never do this inside every request:

```
instantiate model
load weights
build transforms repeatedly
```
That will destroy performance.

Instead:

```
initialize both models during app startup
retain them in memory for all incoming requests
```
## 14.4 If the .pth Contains Full Serialized Models

If the saved file is a full model object rather than a state dictionary, loading becomes more fragile.
Recommended long-term fix:

```
standardize both model files to state_dict-based loading
```
But if full-model serialization is currently used, isolate that in ml/models/loader.py and
document it clearly.

## 15. CPU Inference Flow

Current deployment target is **CPU-only**.


## 15.1 Request-Time Flow

1. accept upload
2. validate file
3. decode audio
4. preprocess waveform
5. generate features
6. run Mel model on CPU
7. run LFCC model on CPU
8. average probabilities
9. persist result
10. return JSON response

## 15.2 CPU Performance Considerations

Because both models run for every request, optimize:

```
model startup loading
feature extraction efficiency
unnecessary tensor copying
repeated transform re-initialization
file I/O overhead
request size limits
```
## 15.3 Practical CPU Considerations

Recommended design choices:

```
keep transforms initialized once if possible
avoid saving uploaded files permanently unless needed
use temp storage for request-local processing
limit maximum file duration and size
use worker count appropriate to CPU cores
benchmark actual latency under concurrent load
```
## 15.4 Future GPU Extensibility

Even though the current system is CPU-only, the architecture should abstract:

```
device selection
tensor movement
model registry
inference runner
```
That allows future migration to GPU without rewriting the API contract.

## 16. API Design

Use versioned APIs from day one.

Base path recommendation:

/api/v1/

## 16.1 API Table


```
Method Endpoint Purpose
GET /api/v1/health Health check
GET /api/v1/version Service version info
POST /api/v1/predict/audio Upload one audio file and get prediction
GET /api/v1/predictions/{id} Fetch one prediction result
GET /api/v1/predictions/historyList authenticated user's prediction history
POST /api/v1/auth/login Login
POST /api/v1/auth/logout Logout
GET /api/v1/auth/me Current user info
GET /admin/ Django admin panel
```
## 17. Request and Response Contracts

## 17.1 Predict Audio Request

**Endpoint**

POST /api/v1/predict/audio
Content-Type: multipart/form-data
Authorization: Bearer <token>

**Form fields**

```
audio_file : required
request_id : optional client correlation id
```
## 17.2 Success Response Example

{
"success": true,
"prediction_id": "0c1fb8bb-8d8e-4d7c-8674-83a0f8c1d441",
"label": "fake",
"confidence": 0.9274,
"probabilities": {
"real": 0.0726,
"fake": 0.
},
"model_outputs": {
"mel": {
"real": 0.0811,
"fake": 0.
},
"lfcc": {
"real": 0.0641,
"fake": 0.
}
},
"ensemble": "average_probability",
"audio": {
"original_filename": "sample.wav",
"duration_seconds_input": 7.2,
"duration_seconds_used": 5.0,
"sample_rate_used": 16000,
"channels_used": 1
},
"timing": {
"preprocessing_ms": 142,
"inference_ms": 88,
"total_ms": 251
},
"model_version": {


"mel": "resnet18_mel_v1",
"lfcc": "resnet18_lfcc_v1"
},
"request_id": "client-123"
}

## 17.3 Error Response Example

{
"success": false,
"error": {
"code": "INVALID_AUDIO_FORMAT",
"message": "Only wav, mp3, and flac files are supported.",
"details": {
"received_content_type": "application/octet-stream"
}
},
"request_id": "client-123"
}

## 17.4 Health Response Example

{
"success": true,
"status": "ok",
"service": "deepfake-audio-backend",
"models": {
"mel_loaded": true,
"lfcc_loaded": true
},
"database": "ok"
}

## 18. Request Flow Sequence Diagram

sequenceDiagram participant Client participant Nginx participant FastAPI participant Preprocess
participant MelModel participant LFCCModel participant DB Client->>Nginx: POST
/api/v1/predict/audio (multipart file) Nginx->>FastAPI: Forward request FastAPI->>FastAPI:
Authenticate + validate request FastAPI->>Preprocess: Decode, trim, resample, mono, fix 5 sec
Preprocess-->>FastAPI: Mel tensor + LFCC tensor FastAPI->>MelModel: Predict mel
probabilities MelModel-->>FastAPI: P_mel(real), P_mel(fake) FastAPI->>LFCCModel: Predict
lfcc probabilities LFCCModel-->>FastAPI: P_lfcc(real), P_lfcc(fake) FastAPI->>FastAPI:
Average probabilities, determine label/confidence FastAPI->>DB: Save prediction metadata and
result DB-->>FastAPI: Prediction ID FastAPI-->>Nginx: JSON response Nginx-->>Client: Final
result

## 19. Sync vs Async Processing

## 19.1 Synchronous Inference

Recommended for the first release if:

```
one file per request
inference latency is acceptable
audio length is limited
traffic volume is moderate
```
Good for:

```
simple frontend integration
```

```
immediate results
easier debugging
```
## 19.2 Asynchronous Job-Based Processing

Recommended later if:

```
batch uploads are introduced
longer processing times appear
traffic spikes become common
frontend timeouts must be avoided
```
Pattern:

1. upload file
2. return job_id
3. process in background
4. client polls result endpoint

## 19.3 Recommendation

Start with **synchronous inference** for single-file prediction.

Add async jobs later for:

```
batch prediction
heavy feature extraction
large file workflows
```
## 20. Database Design

Use PostgreSQL in production.

## 20.1 Recommended Tables

**users**

Use Django’s auth user model or a custom user model.

Fields:

```
id
email / username
password hash
is_active
is_staff
created_at
updated_at
```
**uploaded_audio**

Stores metadata for uploaded files.

Fields:

```
id
user_id
original_filename
```

```
stored_path
mime_type
file_size_bytes
input_duration_seconds
sample_rate_detected
uploaded_at
```
**prediction**

Stores final and per-model inference outputs.

Fields:

```
id
user_id
uploaded_audio_id
final_label
final_confidence
final_prob_real
final_prob_fake
mel_prob_real
mel_prob_fake
lfcc_prob_real
lfcc_prob_fake
ensemble_method
model_version_mel
model_version_lfcc
preprocessing_ms
inference_ms
total_ms
request_id
created_at
```
**model_registry**

Tracks active model versions.

Fields:

```
id
model_name
model_type
version
weight_path
label_map
is_active
created_at
```
**audit_log**

Stores important user/system events.

Fields:

```
id
user_id
action
endpoint
status_code
ip_address
metadata_json
created_at
```

## 20.2 Notes

```
Use UUIDs for external-facing identifiers
Keep raw model probabilities for debugging
Store timing metrics
Avoid storing full raw audio permanently unless required
Separate uploaded file metadata from prediction outputs
```
## 21. Security

Security matters from the first day.

## 21.1 Authentication

Recommended options:

```
JWT access + refresh token
or secure session-based auth if same-domain frontend
```
For frontend/API use, JWT is usually simpler.

## 21.2 Authorization

Enforce:

```
authenticated access to prediction history
access only to user-owned prediction records
admin-only access to model/admin dashboards
```
## 21.3 CORS

Restrict allowed origins explicitly.

Do not use open wildcard CORS in production if credentials or auth headers are involved.

Example allowed origins:

```
http://localhost:
https://app.example.com
```
## 21.4 Upload Validation

Enforce:

```
accepted extensions only
accepted MIME types only
maximum file size
maximum duration if applicable
decoding success check
filename sanitization
quarantine or temporary storage handling
```
## 21.5 File Size / Type Restrictions

Recommended initial restrictions:

```
max upload size: 10 MB to 25 MB depending on expected audio quality
```

```
max request file count: 1
supported types only
```
## 21.6 Rate Limiting

Protect the service using:

```
per-user rate limit
per-IP rate limit
optional burst control
```
This prevents abuse and CPU exhaustion.

## 21.7 Secure Filenames

Never trust the original filename.

Use:

```
generated UUID names
safe extension mapping
isolated storage path
```
## 21.8 Secrets Management

Never hardcode:

```
secret keys
DB credentials
token secrets
model paths for different environments
```
Use environment variables.

## 21.9 Logging Security

Do not log:

```
raw tokens
passwords
sensitive user data
full uploaded file contents
```
Log only safe metadata.

## 22. Frontend Integration

This backend is designed to support frontend integration later without major changes.

## 22.1 Stable API Contracts

Use stable JSON keys from day one.

Frontend should not depend on internal implementation details.

## 22.2 CORS Configuration


Set explicit origins for:

```
local development
staging frontend
production frontend
```
## 22.3 Authentication Pattern

Recommended for SPA frontend:

```
login -> receive access token + refresh token
include access token in Authorization header
refresh when expired
```
## 22.4 Error Format

Use a consistent error contract:

{
"success": false,
"error": {
"code": "SOME_ERROR_CODE",
"message": "Human readable message",
"details": {}
},
"request_id": "optional"
}

## 22.5 Future Polling Option

If asynchronous jobs are added later:

```
POST /api/v1/predict/audio -> returns job_id
GET /api/v1/jobs/{id} -> job status
GET /api/v1/predictions/{id} -> final result
```
## 22.6 Environment Separation

Frontend should use separate API base URLs:

```
local
staging
production
```
Example:

[http://localhost:8000/api/v1](http://localhost:8000/api/v1)
https://staging-api.example.com/api/v1
https://api.example.com/api/v1

## 23. Deployment Strategy

## 23.1 Local Development

Use:

```
Python virtual environment
local PostgreSQL or SQLite for quick bootstrap
local file storage
```

```
Uvicorn
CPU inference
```
## 23.2 Staging

Use:

```
Docker Compose
PostgreSQL
Nginx
Uvicorn/Gunicorn
realistic environment variables
test model weights
```
## 23.3 Production

Use:

```
Docker
Nginx reverse proxy
Gunicorn/Uvicorn worker setup
PostgreSQL
Redis optionally for async jobs / caching
persistent logging
health checks
backup strategy
```
## 23.4 Deployment Diagram

flowchart LR User[Client / Frontend] --> CDN[Optional CDN / WAF] CDN --> Nginx[Nginx
Reverse Proxy] Nginx --> App[App Container: Django + FastAPI] App --> PG[(PostgreSQL)]
App --> Redis[(Redis - Optional)] App --> Vol[Mounted Volume / Object Storage] App -->
Obs[Logs / Metrics / Monitoring]

## 23.5 Process Layout Recommendation

Option A: single deployable ASGI app wrapping both Django and FastAPI
Option B: two app processes behind Nginx

Recommended for maintainability:

```
keep Django and FastAPI in the same repository
allow deployment as:
one app stack initially
split services later if needed
```
## 23.6 Nginx Responsibilities

```
reverse proxy
client max body size enforcement
SSL termination
request buffering
security headers
routing to app services
```
## 23.7 Gunicorn/Uvicorn

Recommended production pattern:


```
Gunicorn managing worker processes
Uvicorn workers serving ASGI app
```
Tune workers based on:

```
CPU cores
average request latency
memory footprint
concurrency needs
```
## 24. Observability

## 24.1 Logging

Log:

```
request id
endpoint
user id if available
file metadata
timing
model versions
outcome
error code
```
Use structured logs in JSON format.

## 24.2 Metrics

Track:

```
request count
success rate
failure rate
p50/p95/p99 latency
preprocessing time
inference time
DB query time
CPU usage
memory usage
```
## 24.3 Tracing Ideas

Useful if the system grows:

```
trace request lifecycle
trace preprocessing duration
trace DB write latency
trace external storage calls
```
## 24.4 Health Checks

Provide:

```
/api/v1/health
readiness check for:
model loaded
DB connectivity
```

```
liveness check for:
process alive
```
## 25. Testing Strategy

Testing must cover both software and ML-serving correctness.

## 25.1 Unit Tests

Test:

```
audio validators
preprocessing functions
ensemble averaging logic
label mapping
error format
model loader behavior
```
## 25.2 Integration Tests

Test:

```
upload + predict flow
DB persistence
auth-protected endpoints
invalid file cases
corrupt audio handling
missing model files
startup failures
```
## 25.3 Contract Tests

Ensure:

```
response keys remain stable
status codes remain stable
error shape remains stable
```
Very important for frontend integration.

## 25.4 Model Regression Tests

Create a locked set of reference audio samples.

Check that:

```
model outputs remain within acceptable tolerance
final labels do not unexpectedly drift
ensemble results are consistent across deployments
```
## 25.5 Load Testing

Test:

```
concurrent uploads
p95 latency
CPU saturation
```

```
worker behavior
error rate under load
```
## 26. Step-by-Step Implementation Roadmap

## Phase 1: Backend Skeleton

```
create Django project
create FastAPI app
set up PostgreSQL
configure settings modules
create local/staging/prod configs
wire logging and environment loading
```
## Phase 2: ML Integration

```
port current preprocessing code into ml/preprocessing
port model architecture code into ml/models
implement model loader
implement CPU inference service
implement ensemble logic
validate output parity with local scripts
```
## Phase 3: API Layer

```
create /api/v1/predict/audio
create /api/v1/health
add request/response schemas
add validation and error handling
add request ids and structured logging
```
## Phase 4: Persistence

```
create DB models
persist upload metadata
persist prediction results
build prediction history endpoint
register admin models
```
## Phase 5: Security and Frontend Readiness

```
add auth
add CORS
add rate limits
add file size restrictions
stabilize contracts for frontend use
```
## Phase 6: Deployment Hardening

```
Dockerize app
add Nginx
configure Gunicorn/Uvicorn
set up staging
run load tests
validate health checks and logs
```

## Phase 7: Production Launch

```
deploy production environment
enable monitoring
finalize backups
run regression suite
freeze model versions
publish API contract
```
## 27. Risks and Common Failure Points

## 27.1 Training/Serving Preprocessing Mismatch

Risk:

```
production accuracy drops because preprocessing differs from training
```
Mitigation:

```
centralize pipeline
regression test with known samples
freeze preprocessing config
```
## 27.2 Wrong Label Order

Risk:

```
real and fake probabilities get swapped
```
Mitigation:

```
explicitly define label map
test known examples
assert order during startup
```
## 27.3 .pth Loading Incompatibility

Risk:

```
state dict mismatch or missing architecture code
```
Mitigation:

```
version model code
document exact architecture
standardize weight loading
```
## 27.4 CPU Saturation

Risk:

```
latency spikes under concurrent requests
```
Mitigation:

```
benchmark properly
tune workers
add async queue later
```

```
rate limit aggressively
```
## 27.5 Invalid Audio Inputs

Risk:

```
decode failures, corrupted files, huge uploads
```
Mitigation:

```
strict validators
safe temp storage
controlled exceptions
```
## 27.6 Silent Failure on Feature Extraction

Risk:

```
malformed feature tensor causes hidden prediction issues
```
Mitigation:

```
assert tensor shapes
log feature dimensions
fail fast on mismatch
```
## 28. Environment Variables

```
Variable Required Example Purpose
```
```
APP_ENV Yes local
```
```
Environment
selection
DEBUG Yes True Debug mode
SECRET_KEY Yes super-secret Django secret
```
```
ALLOWED_HOSTS Yes localhost,127.0.0.1
```
```
Django
allowed hosts
```
```
CORS_ALLOWED_ORIGINS Yes http://localhost:3000
```
```
Allowed
frontend
origins
```
```
DATABASE_URL Yes postgres://user:pass@db:5432/app
```
```
PostgreSQL
connection
REDIS_URL No redis://redis:6379/0 Async/caching
```
```
MEDIA_ROOT Yes /app/media Uploaded
media path
MAX_UPLOAD_SIZE_MB Yes 20 File size limit
```
```
MODEL_MEL_PATH Yes /app/ml/weights/resnet18_mel.pth
```
```
Mel model
weight path
```
```
MODEL_LFCC_PATH Yes /app/ml/weights/resnet18_lfcc.pth
```
```
LFCC model
weight path
```
```
MODEL_LABELS Yes real,fake
```
```
Class label
order
```
```
STANDARD_SAMPLE_RATE Yes 16000
```
```
Required
sample rate
```
```
AUDIO_FIXED_SECONDS Yes 5
```
```
Required
audio duration
ACCESS_TOKEN_SECRET Yes jwt-secret JWT secret
```

```
Variable Required Example Purpose
```
```
ACCESS_TOKEN_EXPIRE_MINUTESYes 60
```
```
Access token
expiry
LOG_LEVEL Yes INFO Logging level
```
## 29. Sample .env.example

APP_ENV=local
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

DATABASE_URL=postgres://postgres:postgres@localhost:5432/deepfake_audio
REDIS_URL=redis://localhost:6379/0

MEDIA_ROOT=./media
MAX_UPLOAD_SIZE_MB=20

MODEL_MEL_PATH=./ml/weights/resnet18_mel.pth
MODEL_LFCC_PATH=./ml/weights/resnet18_lfcc.pth
MODEL_LABELS=real,fake

STANDARD_SAMPLE_RATE=16000
AUDIO_FIXED_SECONDS=5

ACCESS_TOKEN_SECRET=change-this-too
ACCESS_TOKEN_EXPIRE_MINUTES=60

LOG_LEVEL=INFO

## 30. Sample requirements.txt

django>=5.0,<6.0
fastapi>=0.110,<1.0
uvicorn[standard]>=0.29,<1.0
gunicorn>=21.2,<22.0
python-multipart>=0.0.9,<1.0
pydantic>=2.6,<3.0

torch>=2.2,<3.0
torchaudio>=2.2,<3.0
numpy>=1.26,<3.0
scipy>=1.12,<2.0
soundfile>=0.12,<1.0

psycopg2-binary>=2.9,<3.0
python-dotenv>=1.0,<2.0
redis>=5.0,<6.0
celery>=5.3,<6.0

pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
httpx>=0.27,<1.0

## 31. Recommended Implementation Notes

## 31.1 Keep ML Code Isolated

Do not scatter preprocessing logic across routes and utility files. Keep it in:


```
ml/preprocessing/
ml/inference/
ml/models/
```
## 31.2 Keep Request Handlers Thin

FastAPI routes should orchestrate:

```
validation
service calls
response formatting
```
They should not contain heavy ML logic inline.

## 31.3 Store Config Explicitly

Version and centralize:

```
sample rate
audio duration
feature config
label order
ensemble method
```
## 31.4 Add Model Metadata

At startup, log:

```
model paths
versions
label mapping
device
active ensemble method
```
## 32. Example Internal Prediction Service Contract

Example internal flow:

result = prediction_service.predict_audio(
file=uploaded_file,
user=current_user,
request_id=request_id
)

Return object may contain:

```
final probabilities
final label
per-model probabilities
processing timings
persisted prediction id
```
This keeps business logic out of the route layer.

## 33. Acceptance Criteria / Definition of Done

The backend is considered production-ready for v1 when all of the following are true:


### Functional

```
Audio upload endpoint works with supported file types
Both models load successfully at startup
Both models run for every valid request
Final prediction is computed by averaging both model probabilities
Labels are correctly returned as real or fake
Prediction results are stored in the database
Authenticated users can retrieve prediction history
Admin can inspect records via Django admin
```
### Technical

```
Exact training-time preprocessing is reproduced in serving
CPU inference path is benchmarked
Health endpoint reports model and DB readiness
Structured logging is enabled
Error handling is standardized
CORS is configured for the target frontend
Environment-based settings are working
Docker deployment works in staging
```
### Security

```
File size/type validation is enforced
Authentication is enabled for protected endpoints
Rate limiting is configured
Secrets are environment-based
Uploaded filenames are sanitized/generated safely
```
### Quality

```
Unit tests pass
Integration tests pass
Contract tests pass
Model regression tests pass
Load test baseline is documented
```
## 34. Final Recommendation

Build this backend as a **Django-centered application platform with a FastAPI inference layer**
and a clearly isolated **PyTorch ML service**.

For your specific case, the right production design is:

```
Django
```
```
authentication
authorization
admin
ORM
prediction history
operational management
```
```
FastAPI
```
```
versioned inference APIs
```

```
upload handling
typed request/response schemas
frontend-facing contracts
```
```
PyTorch on CPU
```
```
startup-loaded models
exact preprocessing parity
deterministic ensemble inference
```
```
Two-model ensemble
```
```
resnet18_mel.pth
resnet18_lfcc.pth
average probabilities
final label = max averaged probability
```
```
PostgreSQL
```
```
persistence
history
analytics foundation
```
```
Nginx + Gunicorn/Uvicorn
```
```
production serving
```
```
Redis/Celery
```
```
optional now
useful later for async workloads
```
### Practical Build Order

1. port and freeze ML preprocessing/inference
2. implement model loader and ensemble service
3. expose /api/v1/predict/audio
4. persist results to DB
5. add auth and history endpoints
6. harden with logging, CORS, rate limiting
7. deploy with Docker + Nginx + PostgreSQL
8. benchmark CPU performance before production launch

This gives you a backend that is:

```
accurate
explainable
maintainable
frontend-ready
production-oriented
extensible for future GPU or async expansion
```
## 35. Suggested Next Deliverables

After this README, the next engineering deliverables should be:

```
actual backend folder scaffold
requirements.txt
docker-compose.yml
Django models
FastAPI route definitions
```

```
ML loader service
ensemble inference service
health checks
initial test suite
```
If implemented in this structure, the project will be ready for frontend integration and production
hardening without major rework.
