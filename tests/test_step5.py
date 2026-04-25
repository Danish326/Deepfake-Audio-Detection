"""
Step 5 verification: JWT Authentication

Tests:
  1. POST /api/v1/predict/audio without auth -> 401 Unauthorized
  2. POST /api/v1/auth/login with bad credentials -> 401 Unauthorized
  3. POST /api/v1/auth/login with good credentials -> 200 OK & returns JWT
  4. GET /api/v1/auth/me with JWT -> 200 OK
  5. POST /api/v1/predict/audio with JWT -> 200 OK
  6. Query DB -> verify Prediction is linked to User
"""
import os
import glob
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.contrib.auth import get_user_model
from starlette.testclient import TestClient
from config.asgi import application
from apps.predictions.models import Prediction
from apps.uploads.models import UploadedAudio

User = get_user_model()

# Setup test user
test_username = "test_user_step5"
test_password = "securepassword123"
user, created = User.objects.get_or_create(username=test_username, email="test@example.com")
user.set_password(test_password)
user.save()

# Find audio file
audio_file = None
for ext in ['*.wav', '*.mp3', '*.flac']:
    files = glob.glob(r"d:\FAST UNIVERSITY\FYP\Dataset\**\\" + ext, recursive=True)
    if files:
        audio_file = files[0]
        break

if not audio_file:
    import tempfile, numpy as np, soundfile as sf
    wave = (np.sin(2 * np.pi * 440 * np.linspace(0, 5, 80000)) * 0.5).astype("float32")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, wave, 16000)
    audio_file = tmp.name

with TestClient(application) as client:
    print("=" * 60)
    print("TEST 1: Inference without Auth")
    print("=" * 60)
    with open(audio_file, "rb") as f:
        r1 = client.post("/api/v1/predict/audio", files={"file": (os.path.basename(audio_file), f, "audio/wav")})
    print(f"Status: {r1.status_code}")
    assert r1.status_code == 401, "Should reject unauthenticated request!"
    print("  PASS  Endpoint correctly rejects missing token\n")

    print("=" * 60)
    print("TEST 2: Login Failure")
    print("=" * 60)
    r2 = client.post("/api/v1/auth/login", json={"username": test_username, "password": "wrongpassword"})
    print(f"Status: {r2.status_code}")
    assert r2.status_code == 401, "Should reject bad password!"
    print("  PASS  Login correctly rejects bad credentials\n")

    print("=" * 60)
    print("TEST 3: Login Success & Token Issuance")
    print("=" * 60)
    r3 = client.post("/api/v1/auth/login", json={"username": test_username, "password": test_password})
    print(f"Status: {r3.status_code}")
    assert r3.status_code == 200, f"Login failed: {r3.text}"
    token_data = r3.json()
    access_token = token_data.get("access_token")
    assert access_token, "No access token returned!"
    print(f"  PASS  Received JWT access token (expires in {token_data.get('expires_in')}s)\n")

    auth_headers = {"Authorization": f"Bearer {access_token}"}

    print("=" * 60)
    print("TEST 4: Get Current User Profile (/me)")
    print("=" * 60)
    r4 = client.get("/api/v1/auth/me", headers=auth_headers)
    print(f"Status: {r4.status_code}")
    assert r4.status_code == 200, f"/me failed: {r4.text}"
    me_data = r4.json()
    print(f"  PASS  Profile retrieved for: {me_data.get('username')}\n")

    print("=" * 60)
    print("TEST 5: Inference WITH Auth")
    print("=" * 60)
    with open(audio_file, "rb") as f:
        r5 = client.post("/api/v1/predict/audio", headers=auth_headers, files={"file": (os.path.basename(audio_file), f, "audio/wav")})
    print(f"Status: {r5.status_code}")
    assert r5.status_code == 200, f"Inference failed: {r5.text}"
    pred_id = r5.json().get("prediction_id")
    print(f"  PASS  Inference succeeded, returned Prediction ID: {pred_id}\n")

    print("=" * 60)
    print("TEST 6: Verify User Linked in Database")
    print("=" * 60)
    db_pred = Prediction.objects.get(id=pred_id)
    assert db_pred.user == user, f"Prediction user {db_pred.user} does not match {user}"
    print("  PASS  Prediction record successfully linked to User ID")
    
    db_up = db_pred.uploaded_audio
    assert db_up.user == user, "Upload record not linked to user!"
    print("  PASS  UploadedAudio record successfully linked to User ID")

print("\n" + "=" * 60)
print("ALL STEP 5 VERIFICATION TESTS PASSED")
print("=" * 60)

# Cleanup
user.delete()
