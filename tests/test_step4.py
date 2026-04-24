"""
Step 4 verification: Database Persistence

Tests:
  1. POST /api/v1/predict/audio -> returns prediction_id
  2. Query database for prediction_id -> Prediction record exists
  3. Query database for UploadedAudio -> UploadedAudio record exists
  4. GET /api/v1/health -> database: "ok"
"""
import os
import glob
import json

# Setup Django ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from starlette.testclient import TestClient
from config.asgi import application
from apps.predictions.models import Prediction
from apps.uploads.models import UploadedAudio

# Find a real wav file
audio_file = None
for ext in ['*.wav', '*.mp3', '*.flac']:
    files = glob.glob(
        r"d:\FAST UNIVERSITY\FYP\Dataset\**\\" + ext, recursive=True
    )
    if files:
        audio_file = files[0]
        break

if not audio_file:
    import numpy as np, soundfile as sf, tempfile
    wave = (np.sin(2 * np.pi * 440 * np.linspace(0, 5, 80000)) * 0.5).astype("float32")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, wave, 16000)
    audio_file = tmp.name

print(f"Using audio file: {audio_file}")

with TestClient(application) as client:
    print("=" * 60)
    print("TEST 1: Health Endpoint (Database Check)")
    print("=" * 60)
    r_health = client.get("/api/v1/health")
    print(f"Status: {r_health.status_code}")
    health_data = r_health.json()
    print(f"Database status: {health_data.get('database')}")
    assert health_data.get("database") == "ok", "Database health check failed!"
    print("  PASS  Health check returns 'database': 'ok'\n")


    print("=" * 60)
    print("TEST 2: Inference & Database Persistence")
    print("=" * 60)
    with open(audio_file, "rb") as f:
        r_predict = client.post(
            "/api/v1/predict/audio",
            files={"file": (os.path.basename(audio_file), f, "audio/wav")}
        )

    print(f"Status: {r_predict.status_code}")
    assert r_predict.status_code == 200, f"Inference failed: {r_predict.text}"
    pred_data = r_predict.json()
    prediction_id = pred_data.get("prediction_id")

    print(f"Returned Prediction ID: {prediction_id}")
    assert prediction_id, "Response did not contain a prediction_id!"
    print("  PASS  API returns prediction_id\n")

print("=" * 60)
print("TEST 3: Verify Records in Database")
print("=" * 60)

# 1. Check Prediction
try:
    prediction_record = Prediction.objects.get(id=prediction_id)
    print(f"  PASS  Prediction record found in DB! (Label: {prediction_record.final_label})")
    
    # Check JSON field
    assert "per_model" in pred_data, "Response missing per_model"
    assert len(prediction_record.per_model) == 8, "DB record missing 8 models in per_model JSON"
    print(f"  PASS  per_model JSON saved correctly with {len(prediction_record.per_model)} models")
except Prediction.DoesNotExist:
    print("  FAIL  Prediction record NOT found in DB!")
    exit(1)

# 2. Check UploadedAudio
try:
    upload_record = prediction_record.uploaded_audio
    print(f"  PASS  UploadedAudio record found in DB! (Filename: {upload_record.original_filename})")
    print(f"  PASS  Upload file size in DB: {upload_record.file_size_bytes} bytes")
except UploadedAudio.DoesNotExist:
    print("  FAIL  UploadedAudio record NOT linked/found!")
    exit(1)

print("\n" + "=" * 60)
print("ALL STEP 4 VERIFICATION TESTS PASSED ✅")
print("=" * 60)
