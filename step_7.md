# Step 7 — Subscription & Quota System

> **Status**: ✅ Completed
>
> **Phase mapping**: Phase 7 (new feature — subscription quotas)

---

## What Will Be Built in This Step

This step adds a **backend-enforced subscription system** with 3 plan tiers. Every prediction request is validated against the user's plan limits **before** the ML pipeline runs, preventing abuse at the API level. A user self-registration endpoint is also added.

**Key principle:** Quotas are enforced in the backend database — not the frontend. Even if someone bypasses the UI, the API will reject over-quota requests.

---

## The 3 Plans

| Feature | 🆓 Free | 🔍 Analyst | 🏢 Corporate |
|---------|---------|-----------|--------------|
| Predictions / month | **5** | **500** | **Unlimited** |
| Max audio duration | **1 minute** (60s) | **5 minutes** (300s) | **10 minutes** (600s) |
| Max file size | 20 MB | 20 MB | 50 MB |
| Per-model breakdown | ❌ Hidden | ✅ Full 8-model output | ✅ Full 8-model output |
| Billing period | Rolling 30 days from account creation | Same | Same |
| Price (display only) | $0.00 | $29.99/mo | $99.99/mo |

> **Free plan behaviour:** The `per_model` field in the prediction response will be **empty** (`{}`). Free users only see the final `label`, `confidence`, `prob_real`, and `prob_fake`. This encourages upgrades while still providing the core detection functionality.

> **No payment gateway** — plan upgrades are done by an admin via Django Admin panel. Payment integration will be added in a future step.

---

## Files That Will Be Created / Modified

```
apps/subscriptions/                [NEW APP]
├── __init__.py
├── apps.py
├── models.py                      Plan, Subscription, UsageRecord
├── services.py                    get_user_plan, get_or_create_usage, increment_usage
├── quota.py                       enforce_quota (raises HTTP errors)
├── admin.py                       Django Admin panels for all 3 models
└── migrations/
    ├── __init__.py
    ├── 0001_initial.py            Schema migration (auto-generated)
    └── 0002_seed_plans.py         Data migration — seeds Free, Analyst, Corporate plans

api/
├── routes/
│   ├── auth.py                    [MODIFY] Add POST /api/v1/auth/register
│   ├── predict.py                 [MODIFY] Add quota enforcement + duration check
│   └── quota.py                   [NEW]    GET /api/v1/quota/status
├── schemas/
│   ├── auth.py                    [MODIFY] Add RegisterRequest, RegisterResponse
│   └── quota.py                   [NEW]    QuotaStatusResponse
└── fastapi_app.py                 [MODIFY] Register quota router

config/settings/
└── base.py                        [MODIFY] Add "apps.subscriptions" to INSTALLED_APPS

ml/utils/
└── exceptions.py                  [MODIFY] Add QuotaExceededError

tests/
└── test_step7.py                  [NEW]    Quota & registration test suite
```

---

## Component Details

### 1. Database Models (`apps/subscriptions/models.py`)

#### `Plan` — Defines available plan tiers

```python
class Plan(models.Model):
    id                          = UUIDField(primary_key)
    name                        = CharField(unique)       # "free", "analyst", "corporate"
    display_name                = CharField               # "Free Plan", "Analyst Plan", etc.
    max_predictions_per_month   = IntegerField            # 5, 500, -1 (unlimited)
    max_audio_duration_seconds  = IntegerField            # 60, 300, 600
    max_upload_size_mb          = IntegerField            # 20, 20, 50
    show_per_model_breakdown    = BooleanField            # False, True, True
    price_monthly               = DecimalField            # 0.00, 29.99, 99.99
    is_active                   = BooleanField            # Soft-disable without deletion
    created_at                  = DateTimeField
```

Seeded via data migration with 3 default rows.

#### `Subscription` — Links a user to a plan

```python
class Subscription(models.Model):
    id          = UUIDField(primary_key)
    user        = OneToOneField(User)       # One active subscription per user
    plan        = ForeignKey(Plan)
    status      = CharField                 # "active", "cancelled", "expired"
    started_at  = DateTimeField             # When the current period began
    expires_at  = DateTimeField(null=True)  # Null = never expires (free plan)
    created_at  = DateTimeField
```

- `OneToOneField` ensures each user has exactly **one** subscription
- Auto-created with the Free plan when a user registers

#### `UsageRecord` — Tracks predictions per billing period

```python
class UsageRecord(models.Model):
    id                = UUIDField(primary_key)
    user              = ForeignKey(User)
    subscription      = ForeignKey(Subscription)
    period_start      = DateTimeField         # Start of the 30-day window
    period_end        = DateTimeField         # End of the 30-day window
    predictions_used  = PositiveIntegerField  # Incremented on each prediction
    updated_at        = DateTimeField
```

- A new record is created for each 30-day billing period
- `period_start` = user's `created_at` + (N × 30 days), where N is the number of elapsed periods

---

### 2. Business Logic (`apps/subscriptions/services.py`)

```python
def get_user_plan(user) -> Plan:
    """
    Returns the user's active plan.
    If user has no subscription, auto-creates one on the Free plan.
    """

def get_or_create_usage(user, subscription) -> UsageRecord:
    """
    Returns the current billing period's usage record.
    If the current period has expired, creates a fresh record
    with predictions_used=0 for the new period.
    
    Period calculation:
        period_start = user.created_at + (N * 30 days)
        where N = number of complete 30-day windows since account creation
    """

def increment_usage(user) -> None:
    """Called after a successful prediction to bump the counter."""

def get_quota_status(user) -> dict:
    """Returns a dict with plan details + current usage for the API response."""
```

---

### 3. Quota Enforcement (`apps/subscriptions/quota.py`)

```python
def enforce_quota(user, audio_duration_seconds: float) -> Plan:
    """
    Validates the user's request against their plan limits.
    Called BEFORE inference runs — fails fast to save compute.
    
    Checks (in order):
    1. Subscription status — must be "active"
    2. Audio duration — must be within plan's max
    3. Monthly prediction count — must not exceed plan's limit
    
    Returns the Plan object (needed to check show_per_model_breakdown later).
    
    Raises:
        HTTPException 403 SUBSCRIPTION_EXPIRED
        HTTPException 403 AUDIO_TOO_LONG
        HTTPException 403 QUOTA_EXCEEDED
    """
```

---

### 4. Predict Route Changes (`api/routes/predict.py`)

```python
# BEFORE (current):
async def predict_audio(file, request_id, user):
    _validate_file(filename, size)
    audio_bytes = await file.read()
    result = predict(audio_bytes)
    # ... return full response

# AFTER (with quota):
async def predict_audio(file, request_id, user):
    _validate_file(filename, size)
    audio_bytes = await file.read()
    
    # NEW: Get audio duration (lightweight — just reads header, no full decode)
    duration = get_audio_duration(audio_bytes)
    
    # NEW: Enforce quota — raises 403 if exceeded
    plan = await sync_to_async(enforce_quota)(user, duration)
    
    result = predict(audio_bytes)
    
    # NEW: Increment usage counter
    await sync_to_async(increment_usage)(user)
    
    # NEW: Conditionally hide per_model breakdown
    per_model = {}  # empty for Free users
    if plan.show_per_model_breakdown:
        per_model = { ... }  # full 8-model breakdown (existing logic)
    
    return PredictionResponse(per_model=per_model, ...)
```

---

### 5. User Registration (`api/routes/auth.py`)

```python
@router.post("/register")
async def register(request: RegisterRequest):
    """
    Create a new user account.
    
    1. Validate username/email uniqueness
    2. Create Django User
    3. Auto-create Free plan subscription
    4. Return JWT token (user is immediately logged in)
    
    Request:  { "username": "...", "email": "...", "password": "..." }
    Response: { "access_token": "...", "token_type": "bearer", "expires_in": 86400 }
    """
```

---

### 6. Quota Status Endpoint (`api/routes/quota.py`)

```
GET /api/v1/quota/status    (requires Bearer token)

Response 200:
{
  "success": true,
  "plan": {
    "name": "free",
    "display_name": "Free Plan",
    "max_predictions_per_month": 5,
    "max_audio_duration_seconds": 60,
    "max_upload_size_mb": 20,
    "show_per_model_breakdown": false,
    "price_monthly": "0.00"
  },
  "usage": {
    "predictions_used": 3,
    "predictions_limit": 5,
    "predictions_remaining": 2,
    "period_start": "2026-05-05T00:00:00Z",
    "period_end": "2026-06-04T00:00:00Z"
  }
}
```

---

### 7. New Error Responses

| HTTP | Code | Message | When |
|------|------|---------|------|
| 403 | `QUOTA_EXCEEDED` | "You have used all 5 predictions for this billing period. Upgrade your plan for more." | Monthly limit reached |
| 403 | `AUDIO_TOO_LONG` | "Audio duration 72.3s exceeds your plan's limit of 60s. Upgrade for longer audio." | Duration exceeds plan |
| 403 | `SUBSCRIPTION_EXPIRED` | "Your subscription has expired. Please renew or contact support." | Status ≠ active |
| 409 | `USERNAME_TAKEN` | "Username already exists." | Registration conflict |
| 409 | `EMAIL_TAKEN` | "Email already registered." | Registration conflict |

---

### 8. Django Admin

All 3 models registered with rich admin panels:

**Plan Admin:**
- List: name, display_name, max_predictions, price, is_active
- Editable inline — admin can adjust limits without code changes

**Subscription Admin:**
- List: user, plan, status, started_at, expires_at
- Filters: by plan, by status
- Action: "Upgrade to Analyst" / "Upgrade to Corporate" bulk actions

**UsageRecord Admin:**
- List: user, period_start, period_end, predictions_used
- Read-only — no accidental modification of usage counts

---

## Test Cases (`tests/test_step7.py`)

### Registration Tests

| # | Test | Expected |
|---|------|----------|
| R1 | `POST /auth/register` with valid data | `200` — JWT returned, user created |
| R2 | `POST /auth/register` with duplicate username | `409 USERNAME_TAKEN` |
| R3 | `POST /auth/register` with duplicate email | `409 EMAIL_TAKEN` |
| R4 | `POST /auth/register` with weak password | `400` — validation error |
| R5 | New user has Free plan subscription auto-created | Verify in DB |
| R6 | New user can immediately call `/predict/audio` | `200` with JWT from registration |

### Quota Enforcement Tests — Free Plan

| # | Test | Expected |
|---|------|----------|
| Q1 | Free user, 0 predictions made, 30s audio | `200` — prediction succeeds |
| Q2 | Free user, 4 predictions made, 30s audio | `200` — 5th prediction succeeds |
| Q3 | Free user, 5 predictions made, 30s audio | `403 QUOTA_EXCEEDED` |
| Q4 | Free user, 0 predictions, 61s audio | `403 AUDIO_TOO_LONG` |
| Q5 | Free user, 0 predictions, 60s audio | `200` — exactly at limit |
| Q6 | Free user, response `per_model` field | `per_model` is `{}` (empty) |
| Q7 | Free user, response has `label` and `confidence` | Present and correct |

### Quota Enforcement Tests — Analyst Plan

| # | Test | Expected |
|---|------|----------|
| Q8 | Analyst user, 499 predictions, 120s audio | `200` — succeeds |
| Q9 | Analyst user, 500 predictions | `403 QUOTA_EXCEEDED` |
| Q10 | Analyst user, 301s audio | `403 AUDIO_TOO_LONG` |
| Q11 | Analyst user, response has full `per_model` | 8 entries present |

### Quota Enforcement Tests — Corporate Plan

| # | Test | Expected |
|---|------|----------|
| Q12 | Corporate user, 9999 predictions | `200` — always allowed (unlimited) |
| Q13 | Corporate user, 600s audio | `200` — at the limit |
| Q14 | Corporate user, 601s audio | `403 AUDIO_TOO_LONG` |
| Q15 | Corporate user, response has full `per_model` | 8 entries present |

### Billing Period Tests

| # | Test | Expected |
|---|------|----------|
| P1 | User created 29 days ago, 5 predictions used | `403 QUOTA_EXCEEDED` |
| P2 | User created 31 days ago, 5 predictions in old period | `200` — new period, counter reset to 0 |
| P3 | `GET /quota/status` shows correct `period_start` and `period_end` | Matches 30-day window from `created_at` |
| P4 | `GET /quota/status` shows `predictions_remaining = limit - used` | Correct math |

### Subscription Status Tests

| # | Test | Expected |
|---|------|----------|
| S1 | User with `status="cancelled"` subscription | `403 SUBSCRIPTION_EXPIRED` |
| S2 | User with `status="expired"` subscription | `403 SUBSCRIPTION_EXPIRED` |
| S3 | User with no subscription (edge case) | Auto-created on Free, then checked |

### Quota Status Endpoint Tests

| # | Test | Expected |
|---|------|----------|
| E1 | `GET /quota/status` without token | `401 Unauthorized` |
| E2 | `GET /quota/status` with valid token, Free plan | Returns plan details + usage |
| E3 | `GET /quota/status` with Corporate plan | `predictions_remaining = -1` (unlimited) |

### Admin Tests (Manual)

| # | Test | Expected |
|---|------|----------|
| A1 | View Plans in Django Admin | 3 plans listed (Free, Analyst, Corporate) |
| A2 | Change user's subscription to Analyst | User can now make 500 predictions |
| A3 | View UsageRecord for a user | Shows correct prediction count |
| A4 | Create a new custom plan via admin | Works, can be assigned to users |

---

## What Is Explicitly NOT Done in This Step

- No payment gateway (Stripe, PayPal) — admin-assigned plans only
- No automatic plan expiration / downgrade on non-payment
- No webhook for payment events
- No invoice generation
- No refund handling
- No rate limiting per-second (this is per-month quota only)

---

## Success Criteria for This Step

- [ ] `POST /api/v1/auth/register` creates user + Free subscription
- [ ] Free user blocked at 6th prediction with `403 QUOTA_EXCEEDED`
- [ ] Free user blocked for audio > 60 seconds with `403 AUDIO_TOO_LONG`
- [ ] Free user sees empty `per_model` in response
- [ ] Analyst/Corporate users see full `per_model` breakdown
- [ ] `GET /api/v1/quota/status` returns correct plan + usage
- [ ] Billing period resets after 30 days from account creation
- [ ] Django Admin shows Plans, Subscriptions, UsageRecords
- [ ] Admin can upgrade a user's plan and it takes effect immediately
- [ ] All test cases pass

---

> ✅ **Approve this step to begin implementation.**
> Once implemented, this file will be updated with a summary of what was actually built.
