# Cursor Explanation

## What I understood about this project

This repository is for a **deepfake audio detection backend** designed to classify uploaded speech audio as `real` or `fake`.

The system architecture uses:
- **Django** for platform and business concerns (authentication, ORM/database models, admin panel, audit/history management)
- **FastAPI** for inference-focused API endpoints (typed schemas, upload endpoint, health/version APIs)
- **PyTorch (CPU)** for model inference
- **PostgreSQL** for persistent storage of upload and prediction data

## Core inference flow

The backend accepts an audio file and runs a strict preprocessing pipeline:
1. decode audio
2. trim silence
3. resample to 16 kHz
4. convert to mono
5. normalize to fixed 5-second length
6. extract Mel and LFCC features

Then it runs an **8-model ensemble**:
- 4 Mel ResNet18 models (for 4 dataset batches)
- 4 LFCC ResNet18 models (for 4 dataset batches)

Final prediction strategy described in the docs is **most-confident-wins**:
- each model outputs probabilities for `real` and `fake`
- confidence = max(probabilities)
- the model with highest confidence determines final label and confidence

## Important engineering constraints I noticed

- All ML logic should stay inside the `ml/` area (routes should remain thin orchestrators).
- Models must be loaded once at startup and reused (not loaded per request).
- Preprocessing consistency with training-time settings is treated as the most critical reliability factor.
- API responses should remain contract-stable for frontend integration.
- Security expectations include JWT auth, strict upload validation, CORS control, rate limiting, and env-based secrets.

## Operational and quality expectations

- Health endpoint should verify both model readiness and DB connectivity.
- Structured logging and timing metrics are expected for observability.
- Test strategy includes unit, integration, contract, regression, and load testing.
- Deployment path targets Docker + Nginx + Gunicorn/Uvicorn with CPU-based serving initially.

## Notes about other README files found

I also found a few README files inside virtual environment dependency directories (`venv/...`).  
Those are package-maintenance notes and do not describe your application architecture.
