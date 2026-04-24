"""
Step 3 verification: POST /api/v1/predict/audio

Tests:
  1. Valid .wav file          → 200 OK with full prediction
  2. Invalid extension (.txt) → 400 INVALID_FILE_TYPE
  3. Empty file               → 400 EMPTY_FILE
  4. Swagger docs endpoint    → 200 OK
"""
import httpx
import json
import os
import glob

BASE = "http://localhost:8000/api/v1"

# ── Find a real wav file ───────────────────────────────────
audio_file = None
for ext in ['*.wav', '*.mp3', '*.flac']:
    files = glob.glob(
        r"d:\FAST UNIVERSITY\FYP\Dataset\**\\" + ext, recursive=True
    )
    if files:
        audio_file = files[0]
        break

if not audio_file:
    # Fallback: generate a synthetic wav
    import numpy as np, soundfile as sf, tempfile
    wave = (np.sin(2 * np.pi * 440 * np.linspace(0, 5, 80000)) * 0.5).astype("float32")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, wave, 16000)
    audio_file = tmp.name
    print(f"  (using synthetic test tone: {audio_file})")

print(f"Audio file: {audio_file}")
print(f"File size:  {os.path.getsize(audio_file)/1024:.1f} KB\n")

PASS = 0
FAIL = 0

def check(name, condition, details=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}  — {details}")
        FAIL += 1

# ── Test 1: Valid audio file → 200 ─────────────────────────
print("=" * 55)
print("TEST 1: Valid .wav upload")
print("=" * 55)
with open(audio_file, "rb") as f:
    r = httpx.post(
        f"{BASE}/predict/audio",
        files={"file": (os.path.basename(audio_file), f, "audio/wav")},
        timeout=120,
    )

print(f"  HTTP {r.status_code}")
check("Status code 200", r.status_code == 200, r.text[:200])

if r.status_code == 200:
    body = r.json()
    check("success=true",          body.get("success") is True)
    check("label in {real,fake}",  body.get("label") in {"real", "fake"})
    check("confidence 0-1",        0 <= body.get("confidence", -1) <= 1)
    check("winning_model present", bool(body.get("winning_model")))
    check("models_ran = 8",        body.get("models_ran") == 8)
    check("per_model has 8 keys",  len(body.get("per_model", {})) == 8)
    check("processing_time_ms > 0",body.get("processing_time_ms", 0) > 0)
    check("request_id present",    bool(body.get("request_id")))
    check("filename present",      bool(body.get("filename")))
    print(f"\n  label={body['label'].upper()}  confidence={body['confidence']:.4f}  winner={body['winning_model']}")

# ── Test 2: Wrong extension → 400 ──────────────────────────
print()
print("=" * 55)
print("TEST 2: Invalid extension (.txt file)")
print("=" * 55)
r2 = httpx.post(
    f"{BASE}/predict/audio",
    files={"file": ("test.txt", b"not an audio file", "text/plain")},
    timeout=10,
)
print(f"  HTTP {r2.status_code}")
check("Status code 400", r2.status_code == 400, r2.text[:200])
if r2.status_code == 400:
    err = r2.json()
    check("error code INVALID_FILE_TYPE", err.get("detail", {}).get("code") == "INVALID_FILE_TYPE")

# ── Test 3: Empty file → 400 ───────────────────────────────
print()
print("=" * 55)
print("TEST 3: Empty file")
print("=" * 55)
r3 = httpx.post(
    f"{BASE}/predict/audio",
    files={"file": ("silent.wav", b"", "audio/wav")},
    timeout=10,
)
print(f"  HTTP {r3.status_code}")
check("Status code 400", r3.status_code == 400, r3.text[:200])
if r3.status_code == 400:
    err = r3.json()
    check("error code EMPTY_FILE", err.get("detail", {}).get("code") == "EMPTY_FILE")

# ── Test 4: Swagger docs ────────────────────────────────────
print()
print("=" * 55)
print("TEST 4: Swagger UI docs endpoint")
print("=" * 55)
r4 = httpx.get(f"{BASE}/docs", timeout=10)
print(f"  HTTP {r4.status_code}")
check("Swagger UI returns 200", r4.status_code == 200)
check("predict/audio in OpenAPI", "predict" in httpx.get(f"{BASE}/openapi.json").text)

# ── Summary ─────────────────────────────────────────────────
print()
print("=" * 55)
print(f"Results: {PASS} passed, {FAIL} failed")
print("=" * 55)
