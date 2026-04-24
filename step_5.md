# Step 5 — Authentication (JWT)

> **Status**: 🟡 Awaiting Approval
>
> **Phase mapping**: Phase 5 from the spec (`project-software-specification.md`)

---

## What Will Be Built in This Step

This step introduces security and user management. We will implement JSON Web Token (JWT) authentication using FastAPI, integrating seamlessly with the existing Django `User` model. 

By the end of this step, the inference endpoint will be protected, and users will need to log in to submit audio files. All predictions will be permanently linked to the user who requested them.

**Key Features:**
- `POST /api/v1/auth/login`: Accepts username/password, validates against the Django database, and returns a signed JWT.
- `GET /api/v1/auth/me`: Returns the currently authenticated user's profile.
- **Endpoint Protection**: The `POST /api/v1/predict/audio` endpoint will require a valid JWT `Bearer` token.
- **User Traceability**: The `Upload` and `Prediction` records created in Step 4 will now accurately record which user made the request.

---

## Files That Will Be Created / Modified

```
requirements.txt             [MODIFY] Add `PyJWT` for token generation/verification
api/
├── routes/
│   ├── auth.py              [NEW]  Login, logout, and /me endpoints
│   └── predict.py           [MODIFY] Add `Depends(get_current_user)` and link User to DB records
├── schemas/
│   └── auth.py              [NEW]  LoginRequest, TokenResponse, UserResponse
├── dependencies.py          [MODIFY] Add `get_current_user` dependency to validate JWTs
└── fastapi_app.py           [MODIFY] Register auth router
```

---

## Component Details

### 1. New Dependency (`api/dependencies.py`)
We will create a `get_current_user` dependency. When attached to an endpoint, it will:
1. Extract the `Bearer` token from the `Authorization` header.
2. Decode and verify the JWT signature using Django's `SECRET_KEY`.
3. Extract the `user_id` from the token payload.
4. Use Django's ORM (via `sync_to_async`) to fetch the `User` object.
5. Raise an HTTP 401 Unauthorized error if any step fails.

### 2. Auth Routes (`api/routes/auth.py`)
- **Login**: We will use Django's built-in `authenticate()` function to verify credentials securely without having to reimplement password hashing logic. If valid, a JWT is minted with a 24-hour expiration.
- **Logout**: Since JWTs are stateless, logout will simply be a stub endpoint that tells the frontend to discard the token, returning a success message.

### 3. Inference Updates (`api/routes/predict.py`)
- The signature will change to include `user: User = Depends(get_current_user)`.
- The `create_prediction_record` call will be updated to pass `user=user`, linking the ML inference to the specific account.

---

## Success Criteria for This Step

- [ ] `PyJWT` is successfully installed and added to `requirements.txt`.
- [ ] `POST /api/v1/auth/login` successfully returns a JWT for valid Django users.
- [ ] `GET /api/v1/auth/me` returns the correct user profile when provided a valid token.
- [ ] `POST /api/v1/predict/audio` rejects unauthenticated requests with a `401 Unauthorized`.
- [ ] Authenticated predictions successfully save the `user_id` to the database.

---

> ✅ **Approve this step to begin implementation.**
> Once implemented, this file will be updated with a summary of what was actually built.
