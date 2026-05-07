# Step 4 — Database Persistence

> **Status**: ✅ Implemented
>
> **Phase mapping**: Phase 4 from the spec (`project-software-specification.md`)

---

## ✅ Implementation Summary

During Step 4, we discovered that most of the database wiring was already implemented in the codebase! Here is what was verified and the final missing piece that was fixed:

| File | Result |
|---|---|
| `apps/uploads/models.py` | ✅ `UploadedAudio` model exists and stores file metadata. |
| `apps/predictions/models.py` | ✅ `Prediction` model exists and stores full inference results (including `per_model` JSON). |
| `apps/uploads/admin.py` | ✅ Read-only admin panels configured. |
| `apps/predictions/admin.py` | ✅ Read-only admin panels configured. |
| `apps/predictions/services.py` | ✅ `create_prediction_record` correctly creates both database records. |
| `api/routes/predict.py` | ✅ `predict_audio` uses `sync_to_async` to save results without blocking FastAPI, returning `prediction_id`. |
| `api/routes/health.py` | ✅ **Fixed**: Added `connection.ensure_connection()` to actively ping the DB. Health check now returns `"database": "ok"`. |

All database migrations were also verified to be fully applied to the SQLite database.

---

## What Will Be Built in This Step

This step connects the ML pipeline to the PostgreSQL database (via Django's ORM). Every time a user uploads an audio file for prediction, the backend will now save the file metadata and the full inference results.

By the end of this step, the system will maintain a permanent, queryable history of all predictions, which can be viewed through the Django Admin panel.

**Key Features:**
- `Upload` model: Stores file metadata (original filename, size, content type).
- `Prediction` model: Stores the final label, confidence, pipeline timing, and the full probability breakdown for all 8 models.
- **Async ORM**: FastAPI will use Django's `sync_to_async` to securely write to the database without blocking the asynchronous event loop.
- **Admin Views**: Read-only admin panels to inspect past predictions.
- **Health Check**: The `/api/v1/health` endpoint will now actively ping the database to verify connectivity.

---

## Files That Will Be Created / Modified

```
apps/
├── uploads/
│   ├── models.py            [NEW]  Upload model
│   └── admin.py             [NEW]  Upload admin view
├── predictions/
│   ├── models.py            [MODIFY] Prediction model with JSONField for per_model data
│   └── admin.py             [NEW]  Prediction admin view
└── ...

api/
├── routes/
│   ├── predict.py           [MODIFY] Save Upload and Prediction via ORM before returning
│   └── health.py            [MODIFY] Add DB ping check
└── schemas/
    ├── predict.py           [MODIFY] Add `prediction_id` to response
    └── common.py            (no changes)
```

---

## Component Details

### 1. Database Models

**`Upload` Model (`apps/uploads/models.py`)**
- `id`: UUID
- `filename`: String
- `size_bytes`: Integer
- `content_type`: String
- `created_at`: Datetime

**`Prediction` Model (`apps/predictions/models.py`)**
- `id`: UUID
- `upload`: ForeignKey to `Upload`
- `final_label`: String ("real" or "fake")
- `confidence`: Float
- `winning_model`: String
- `models_ran`: Integer
- `per_model_data`: JSONField (stores the exact breakdown returned by the ML pipeline)
- `processing_time_ms`: Float
- `created_at`: Datetime

*(Note: We are not storing the actual audio file bytes on disk or in S3 yet to keep the system stateless and disk-light. We only store the metadata and the prediction result.)*

### 2. FastAPI Route Update (`api/routes/predict.py`)

The existing `POST /api/v1/predict/audio` will be updated to:
1. Validate and run inference (existing logic).
2. Use `asgiref.sync.sync_to_async` to call a Django service function.
3. Create the `Upload` record.
4. Create the `Prediction` record linked to the upload.
5. Return the response, now including a `prediction_id` field so the frontend can reference it later.

### 3. Health Endpoint (`api/routes/health.py`)

The `database` field in the health response currently says `"unknown"`.
We will add a lightweight query (e.g., `await sync_to_async(User.objects.exists)()`) to verify DB connectivity. If it succeeds, `database` becomes `"ok"`. If it fails, `database` becomes `"error"` and the overall status degrades.

### 4. Django Admin

Register `Upload` and `Prediction` in their respective `admin.py` files with `list_display`, `list_filter`, and `search_fields` to make debugging and auditing easy for administrators. Make them read-only to prevent accidental modification of historical ML results.

---

## ✅ Success Criteria Met

- [x] Django migrations generated (`makemigrations`) and applied (`migrate`).
- [x] `POST /api/v1/predict/audio` successfully saves to the database and returns a `prediction_id`.
- [x] `GET /api/v1/health` returns `"database": "ok"`.
- [x] Django Admin panel displays the new Upload and Prediction records.
- [x] The inference speed is not significantly impacted by the DB write (writes are fast and localized).
