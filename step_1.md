# Step 1 — Backend Skeleton

> **Status**: ✅ Implemented
>
> **Phase mapping**: Phase 1 from the spec (`project-software-specification.md`)

---

## ✅ Implementation Summary

All items from the proposal were built and verified. Notes on deviations / decisions made during implementation:

| Item | Result |
|---|---|
| Django project + split settings | ✅ `config/settings/{base,local,staging,production}.py` |
| FastAPI app factory | ✅ `api/fastapi_app.py` with CORS + middleware |
| ASGI dispatcher (Django + FastAPI) | ✅ `config/asgi.py` via `starlette.routing.Mount` |
| Request-ID + Timing middleware | ✅ `api/middleware.py` — values on `request.state` |
| `GET /api/v1/health` | ✅ Returns `200` with all 8 model flags + db status |
| `GET /admin/` | ✅ Django admin login page served |
| `GET /api/v1/docs` | ✅ Swagger UI served by FastAPI |
| Custom User model (UUID PK) | ✅ `apps/users/models.py`, migration generated |
| `ml/utils/constants.py` | ✅ Includes `get_model_filename()` and `get_model_weight_path()` helpers |
| ML weights folder structure | ✅ 4 batch subfolders with `.gitkeep` |
| All placeholder Django apps | ✅ users, predictions, uploads, audit_logs registered |
| `python manage.py migrate` | ✅ Runs cleanly (SQLite in local dev) |
| `uvicorn config.asgi:application` | ✅ Starts without errors |

### Verified Endpoint Responses

```
GET /api/v1/health → 200 OK
{
  "success": true,
  "status": "ok",
  "service": "deepfake-audio-backend",
  "models": { "mel_data3": false, "mel_data5": false, ... (all 8 false — Step 2) },
  "database": "unknown",
  "version": "1.0.0",
  "request_id": "<uuid>"
}

GET /admin/        → 200 OK (Django login page)
GET /api/v1/docs   → 200 OK (Swagger UI)
```

### One Deviation from Plan
`makemigrations` must be run explicitly for `users` before `migrate` — Django requires at least one migration for a custom `AUTH_USER_MODEL`. This was done and the generated migration is committed at `apps/users/migrations/0001_initial.py`. The other apps (predictions, uploads, audit_logs) have empty migration folders — their models are implemented in Step 4.

---

## What Will Be Built in This Step

This step establishes the **entire foundational scaffold** of the project. Nothing ML-specific is touched yet — this is purely about creating a clean, professional project structure that every subsequent step builds on top of.

By the end of this step the repository will have a runnable (though empty) Django + FastAPI application with environment-based configuration, structured logging, and a split settings system.

---

## Files & Directories That Will Be Created

```
deepfake-audio-backend/
│
├── manage.py                        # Django management entry point
├── requirements.txt                 # All pinned Python dependencies
├── .env                             # Local dev secrets (git-ignored)
├── .env.example                     # Template for env vars (committed)
├── .gitignore                       # Python / Django / IDE ignores
│
├── config/                          # Django project package
│   ├── __init__.py
│   ├── asgi.py                      # ASGI entry point (mounts Django + FastAPI)
│   ├── wsgi.py                      # WSGI entry point (optional fallback)
│   ├── urls.py                      # Root Django URL conf
│   └── settings/
│       ├── __init__.py              # Auto-selects settings module via APP_ENV
│       ├── base.py                  # Shared settings (all environments)
│       ├── local.py                 # Local dev overrides
│       ├── staging.py               # Staging overrides
│       └── production.py            # Production overrides
│
├── api/                             # FastAPI application package
│   ├── __init__.py
│   ├── fastapi_app.py               # FastAPI app factory (create_app())
│   ├── dependencies.py              # Shared FastAPI dependencies (placeholder)
│   ├── middleware.py                # Request ID injection, timing middleware
│   ├── routes/
│   │   ├── __init__.py
│   │   └── health.py                # GET /api/v1/health  (stub response)
│   └── schemas/
│       ├── __init__.py
│       └── common.py                # Shared Pydantic response models
│
├── apps/                            # Django app packages (empty shells)
│   ├── users/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Placeholder (custom user model defined)
│   │   ├── admin.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── predictions/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Placeholder
│   │   ├── admin.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── uploads/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Placeholder
│   │   └── migrations/
│   │       └── __init__.py
│   └── audit_logs/
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py                # Placeholder
│       ├── admin.py
│       └── migrations/
│           └── __init__.py
│
├── ml/                              # ML code (empty shells — populated in Step 2)
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── weights/                      # Mirrors training batch structure
│   │   ├── data3/
│   │   │   └── models/
│   │   │       ├── best_resnet18_mel_3.pth
│   │   │       └── best_resnet18_lfcc_3.pth
│   │   ├── data5/
│   │   │   └── models/
│   │   │       ├── best_resnet18_mel_5.pth
│   │   │       └── best_resnet18_lfcc_5.pth
│   │   ├── data6/
│   │   │   └── models/
│   │   │       ├── best_resnet18_mel_6.pth
│   │   │       └── best_resnet18_lfcc_6.pth
│   │   └── data8/
│   │       └── models/
│   │           ├── best_resnet18_mel_8.pth
│   │           └── best_resnet18_lfcc_8.pth
│   ├── preprocessing/
│   │   └── __init__.py
│   ├── inference/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── constants.py             # APP_SAMPLE_RATE, AUDIO_FIXED_SECONDS, etc.
│
├── media/
│   ├── uploads/
│   │   └── .gitkeep
│   └── failed/
│       └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
└── tests/
    ├── __init__.py
    ├── unit/
    │   └── __init__.py
    ├── integration/
    │   └── __init__.py
    ├── contract/
    │   └── __init__.py
    ├── regression/
    │   └── __init__.py
    └── load/
        └── __init__.py
```

---

## What Each Piece Does

### `config/settings/` — Split Settings System

The settings are split across four files rather than one monolithic `settings.py`. This is a standard Django production pattern.

| File | Purpose |
|---|---|
| `base.py` | All settings shared across every environment: installed apps, middleware, auth backends, database config loaded from `DATABASE_URL`, static/media paths, logging config |
| `local.py` | `DEBUG=True`, relaxed security, SQLite fallback if no `DATABASE_URL` set, verbose console logging |
| `staging.py` | `DEBUG=False`, PostgreSQL, realistic CORS, stricter security headers |
| `production.py` | `DEBUG=False`, all hardened settings, no fallbacks allowed |

`config/settings/__init__.py` reads `APP_ENV` from the environment and imports the correct module:

```python
import os
env = os.environ.get("APP_ENV", "local")
if env == "production":
    from .production import *
elif env == "staging":
    from .staging import *
else:
    from .local import *
```

### ⚠️ Key Architecture Change vs. Original Spec

The original spec assumed **2 models** (1 Mel + 1 LFCC) with probability averaging.

The **actual trained system** uses **8 models** across **4 disjoint data batches**:

| Batch | Mel Model | LFCC Model |
|---|---|---|
| data3 | `best_resnet18_mel_3.pth` | `best_resnet18_lfcc_3.pth` |
| data5 | `best_resnet18_mel_5.pth` | `best_resnet18_lfcc_5.pth` |
| data6 | `best_resnet18_mel_6.pth` | `best_resnet18_lfcc_6.pth` |
| data8 | `best_resnet18_mel_8.pth` | `best_resnet18_lfcc_8.pth` |

**Why?** The full dataset was split into 4 non-overlapping batches. No single model has seen the full dataset. To compensate, all 8 models run on every request, and the **most confident prediction wins** (the model with the highest `max(softmax probability)` determines the final label).

The aggregation logic will be fully implemented in Step 2. This step only scaffolds the weight folder structure.

---

### `config/asgi.py` — Mounting Django + FastAPI Together

Instead of running two separate processes, both Django and FastAPI are mounted under a single ASGI application. This is the recommended "Option A" from the spec:

```
/api/v1/*   → FastAPI handles
/admin/*    → Django handles
/*          → Django handles
```

This is achieved using a lightweight ASGI router (e.g., a custom dispatcher or `starlette.routing.Mount`).

### `api/fastapi_app.py` — FastAPI App Factory

Creates and configures the FastAPI application:
- Sets title, version, description
- Registers routers (health route in this step)
- Registers middleware (request ID injection, timing headers)
- Configures CORS (origins from env)

### `api/routes/health.py` — Health Endpoint (Stub)

Returns a minimal health response in this step. Will be expanded in Step 3 to check actual model load status and DB connectivity.

```json
GET /api/v1/health
→ { "success": true, "status": "ok", "service": "deepfake-audio-backend" }
```

### `ml/utils/constants.py` — Frozen Configuration

Centralises all ML/audio constants that must never drift between training and serving:

```python
STANDARD_SAMPLE_RATE = int(os.environ.get("STANDARD_SAMPLE_RATE", 16000))
AUDIO_FIXED_SECONDS  = int(os.environ.get("AUDIO_FIXED_SECONDS", 5))
MODEL_LABELS         = os.environ.get("MODEL_LABELS", "real,fake").split(",")
```

### Structured Logging

Logging is configured in `base.py` using Python's standard `logging` with a JSON formatter for production and a human-readable formatter for local dev. Every log entry will include:
- `timestamp`
- `level`
- `logger`
- `message`
- `request_id` (injected by middleware when available)

---

## Dependencies Installed in This Step

```
# Web / API
django>=5.0,<6.0
fastapi>=0.110,<1.0
uvicorn[standard]>=0.29,<1.0
gunicorn>=21.2,<22.0
python-multipart>=0.0.9,<1.0
pydantic>=2.6,<3.0
starlette>=0.36,<1.0          # already a FastAPI dep, explicit for ASGI routing

# Database
psycopg2-binary>=2.9,<3.0

# Config
python-dotenv>=1.0,<2.0

# Testing (dev only)
pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
httpx>=0.27,<1.0
```

> ML/PyTorch dependencies are **NOT** installed in this step. They are large and will be added in Step 2 when the ML layer is integrated.

---

## How to Run After This Step

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file
copy .env.example .env

# 4. Run initial Django migrations (creates auth tables)
python manage.py migrate

# 5. Start the development server
uvicorn config.asgi:application --reload --port 8000

# 6. Verify health endpoint
# → http://localhost:8000/api/v1/health  should return {"success": true, ...}
# → http://localhost:8000/admin/         should show Django admin login page
```

---

## What Is Explicitly NOT Done in This Step

- No ML models, no PyTorch, no preprocessing code
- No prediction endpoints
- No authentication
- No database models beyond the built-in Django auth tables
- No Docker or Nginx configuration
- No actual health checking of models or DB (stub only)

---

## Success Criteria for This Step

- [ ] `uvicorn config.asgi:application --reload` starts without errors
- [ ] `GET /api/v1/health` returns `200 OK` with correct JSON shape
- [ ] `GET /admin/` shows the Django admin login page
- [ ] `python manage.py migrate` runs cleanly
- [ ] `APP_ENV=local` uses local settings; switching to `staging` or `production` loads correct module
- [ ] All placeholder Django apps are registered in `INSTALLED_APPS`
- [ ] Project structure matches the folder tree above exactly

---

> ✅ **Approve this step to begin implementation.**
> Once implemented, this file will be updated with a summary of what was actually built and any deviations from the plan.
