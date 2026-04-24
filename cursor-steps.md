# Cursor Steps Tracker

This file tracks progress and planning for the backend development workflow.

---

## What has been done (Steps 1-3)

### Step 1 - Backend Skeleton (Completed)
- Created Django + FastAPI project scaffold.
- Added split settings (`base`, `local`, `staging`, `production`).
- Configured ASGI app dispatch for Django and FastAPI.
- Added middleware foundation (request ID and timing support).
- Added initial routes: health endpoint, admin access, and API docs path.
- Registered placeholder domain apps (`users`, `predictions`, `uploads`, `audit_logs`).
- Added base folder structure for ML, media, logs, and tests.

### Step 2 - ML Integration (Completed)
- Ported training-aligned ML components into `ml/`.
- Implemented audio preprocessing pipeline and feature extraction (Mel + LFCC).
- Implemented model loading and in-memory registry for all 8 models.
- Implemented CPU inference flow and result aggregation.
- Wired startup model loading and exposed model health status.

### Step 3 - Inference API Endpoint (Completed)
- Added `POST /api/v1/predict/audio`.
- Added request validation and standardized error responses.
- Connected endpoint to ML predictor service.
- Returned structured inference response including per-model outputs.
- Added schema definitions for prediction response payloads.

---

## Step 4 - Persistence Layer (Planned for approval)

### Goal
Persist upload metadata and prediction results in the database, and expose prediction retrieval/history endpoints for application use.

### Scope for Step 4
- Add core Django models for:
  - uploaded audio metadata
  - prediction records
  - model version registry
  - audit logs (minimal initial structure)
- Save prediction records after successful inference.
- Add endpoint(s) to fetch prediction history and single prediction details.
- Register models in Django admin for inspection.
- Add migrations and ensure schema is consistent.

### Proposed files to create/modify

#### Django models and admin
- `apps/uploads/models.py`
- `apps/predictions/models.py`
- `apps/audit_logs/models.py`
- `apps/predictions/admin.py`
- `apps/uploads/admin.py`
- `apps/audit_logs/admin.py`

#### Services/selectors (if needed for clean orchestration)
- `apps/predictions/services.py`
- `apps/predictions/selectors.py`

#### API routes/schemas integration
- `api/routes/predict.py` (persist results after inference)
- `api/routes/predictions.py` (new history/detail endpoints)
- `api/schemas/predict.py` (include persisted IDs/metadata if required)
- `api/schemas/common.py` (only if shared response shape needs extension)

#### Migrations
- `apps/uploads/migrations/*`
- `apps/predictions/migrations/*`
- `apps/audit_logs/migrations/*`

### API behavior planned in this step
- Keep existing inference endpoint behavior intact.
- Extend flow so successful prediction also writes DB records.
- Add retrieval endpoints under `/api/v1/predictions/...`:
  - get one prediction by ID
  - get prediction history list (initially basic filtering/pagination)

### Out of scope for Step 4
- JWT auth and authorization rules (Step 5).
- Rate limiting (Step 5).
- Deployment hardening (Step 6).
- Production monitoring rollout (Step 7).

### Validation and testing plan
- Model-level tests for DB object creation and constraints.
- Integration tests:
  - upload -> infer -> persist -> retrieve by ID
  - history endpoint returns expected records
- Regression check to ensure Step 3 response contract is not broken.
- Admin page check for created records visibility.

### Acceptance criteria
- Prediction requests create persistent DB records for upload + inference output.
- Retrieval endpoint returns stored prediction by ID.
- History endpoint returns recent prediction list in stable format.
- Django migrations apply cleanly.
- Existing `/api/v1/predict/audio` continues to work.

---

## Approval checkpoint

Step 4 implementation should begin only after explicit approval.
