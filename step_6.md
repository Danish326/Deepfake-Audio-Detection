# Step 6 — Deployment Hardening (Docker)

> **Status**: ✅ Implemented
>
> **Phase mapping**: Phase 6 from the spec (`project-software-specification.md`)

---

## ✅ Implementation Summary

| File | Result |
|---|---|
| `Dockerfile` | ✅ Python 3.10-slim base, OS audio deps (libsndfile1, ffmpeg), pip install |
| `docker-entrypoint.sh` | ✅ collectstatic → migrate → gunicorn with Uvicorn workers |
| `docker-compose.yml` | ✅ 3-service stack: PostgreSQL 15, Backend, Nginx |
| `nginx/nginx.conf` | ✅ Reverse proxy with static/media serving and upload limits |
| `requirements.txt` | ✅ `psycopg2-binary` already present for PostgreSQL |

### Verification

- `docker-compose up --build` successfully built and started all 3 containers
- All endpoints accessible via `http://localhost`:
  - `GET /api/v1/health` → 200 OK
  - `GET /admin/` → Django Admin (CSS loads via Nginx)
  - `POST /api/v1/predict/audio` → ML inference functional
  - `POST /api/v1/auth/login` → JWT issued

---

## What Was Built in This Step

This step transitions the backend from a local development setup (SQLite + `uvicorn --reload`) to a **production-ready Docker environment** with three containers working together.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                     Host Machine                       │
│                                                        │
│   Browser / Postman / Frontend                         │
│         │                                              │
│         ▼ port 80                                      │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │    Nginx     │────▶│   Backend    │                 │
│  │  (port 80)   │     │ (port 8000)  │                 │
│  │              │     │              │                 │
│  │ Static files │     │ Django +     │     ┌────────┐  │
│  │ /static/     │     │ FastAPI +    │────▶│  DB    │  │
│  │ /media/      │     │ ML Models   │     │ PG 15  │  │
│  └──────────────┘     └──────────────┘     └────────┘  │
│   deepfake_nginx       deepfake_backend    deepfake_db │
└────────────────────────────────────────────────────────┘
```

**Three containers, three jobs:**

| Container | Image | Job |
|---|---|---|
| `deepfake_db` | `postgres:15-alpine` | Stores users, predictions, uploads |
| `deepfake_backend` | Custom (Dockerfile) | Runs Django + FastAPI + 8 ML models |
| `deepfake_nginx` | `nginx:alpine` | Reverse proxy, serves static/media files |

---

## File-by-File Walkthrough

### 1. `Dockerfile` — Building the Backend Image

The Dockerfile creates a portable image of the entire Python application.

```dockerfile
FROM python:3.10-slim
```

**Why `python:3.10-slim`?** It's a minimal Debian-based Python image (~45 MB vs ~900 MB for the full image). Smaller images = faster builds, faster deploys, smaller attack surface.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

| Variable | What it does |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1` | Prevents Python from creating `.pyc` cache files inside the container (saves disk space) |
| `PYTHONUNBUFFERED=1` | Forces Python to print output immediately instead of buffering — critical for seeing logs in real-time with `docker logs` |

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

| Package | Why it's needed |
|---|---|
| `build-essential` | C compiler needed to install some Python packages (e.g., `psycopg2`) |
| `libpq-dev` | PostgreSQL client library headers — required by `psycopg2` |
| `libsndfile1` | Audio file reading library — used by `soundfile` (which `librosa` depends on) |
| `ffmpeg` | Audio format decoding — handles MP3, FLAC, and other compressed formats |

The `rm -rf /var/lib/apt/lists/*` at the end cleans up the package cache to keep the image small.

```dockerfile
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
```

**Why copy `requirements.txt` first, then code?** Docker caches each layer. If your code changes but requirements don't, Docker skips the slow `pip install` step. This is called **layer caching** and can save 5–10 minutes on rebuilds.

```dockerfile
COPY . /app/
RUN chmod +x /app/docker-entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

- `COPY . /app/` — copies all application code into the container
- `chmod +x` — makes the startup script executable (required on Linux)
- `EXPOSE 8000` — documents which port the app listens on
- `ENTRYPOINT` — the command that runs when the container starts

---

### 2. `docker-entrypoint.sh` — Startup Script

This script runs every time the backend container starts:

```bash
#!/bin/bash
set -e  # Stop immediately if any command fails

# Step 1: Collect Django admin CSS/JS into /app/staticfiles/
python manage.py collectstatic --noinput

# Step 2: Apply any pending database migrations
python manage.py migrate --noinput

# Step 3: Start the production server
exec gunicorn config.asgi:application \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

**Key concepts:**

| Concept | Explanation |
|---|---|
| `collectstatic` | Django's admin panel uses CSS/JS files. This command copies them into a single folder (`/app/staticfiles/`) that Nginx can serve directly — much faster than making Python serve CSS files |
| `migrate` | Applies database schema changes (creates tables) automatically on startup. Safe to run repeatedly — Django skips already-applied migrations |
| `gunicorn` | A production-grade Python process manager. It spawns multiple **worker processes** to handle concurrent requests |
| `--worker-class uvicorn.workers.UvicornWorker` | Each worker uses Uvicorn (async ASGI server) instead of the default sync WSGI. This is required because FastAPI is an ASGI application |
| `--workers 2` | Spawns 2 worker processes. Each worker loads all 8 ML models independently. More workers = more concurrent requests, but also more RAM |
| `--timeout 120` | If a request takes longer than 120 seconds, the worker is killed and restarted. ML inference can take a few seconds, so 120s gives plenty of headroom |
| `exec` | Replaces the shell process with gunicorn. This ensures Docker signals (like `docker stop`) are sent directly to gunicorn for graceful shutdown |

---

### 3. `docker-compose.yml` — Orchestrating All Containers

Docker Compose defines and runs all three containers as a single stack.

#### Service 1: `db` (PostgreSQL)

```yaml
db:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: deepfake_db
    POSTGRES_USER: deepfake_user
    POSTGRES_PASSWORD: deepfake_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U deepfake_user -d deepfake_db"]
    interval: 5s
    retries: 5
```

| Concept | Explanation |
|---|---|
| `postgres:15-alpine` | Official PostgreSQL 15 image, Alpine variant (smaller) |
| `POSTGRES_*` env vars | PostgreSQL reads these on first startup to create the database and user automatically |
| `volumes: postgres_data` | A **named volume** — data persists even if the container is destroyed. Without this, all data is lost when you run `docker-compose down` |
| `healthcheck` | Docker pings the database every 5 seconds. The backend container **waits** until this reports healthy before starting |

#### Service 2: `backend` (Python Application)

```yaml
backend:
  build: .
  environment:
    APP_ENV: staging
    DATABASE_URL: "postgres://deepfake_user:deepfake_password@db:5432/deepfake_db"
  volumes:
    - ./ml/weights:/app/ml/weights
    - static_volume:/app/staticfiles
    - media_volume:/app/media
  depends_on:
    db:
      condition: service_healthy
```

| Concept | Explanation |
|---|---|
| `build: .` | Build the image using the `Dockerfile` in the current directory |
| `APP_ENV: staging` | Tells Django to use `config/settings/staging.py` which enables PostgreSQL and `DEBUG=False` |
| `DATABASE_URL` | Connection string for PostgreSQL. `db` is the hostname — Docker networking resolves container names automatically |
| `./ml/weights:/app/ml/weights` | **Bind mount** — mounts the weights folder from your host machine into the container. You don't need to rebuild the image when you update model weights |
| `static_volume` / `media_volume` | **Shared volumes** — the backend writes files here, and Nginx reads from the same volumes |
| `depends_on: condition: service_healthy` | The backend won't start until PostgreSQL passes its health check |

#### Service 3: `nginx` (Reverse Proxy)

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - static_volume:/app/staticfiles:ro
    - media_volume:/app/media:ro
  depends_on:
    - backend
```

| Concept | Explanation |
|---|---|
| `ports: "80:80"` | Maps port 80 on your machine to port 80 in the container. This is the **only** port exposed to the outside world |
| `:ro` | Read-only mount — Nginx only needs to read these files, never write |
| `depends_on: backend` | Ensures backend starts before Nginx (so there's something to proxy to) |

---

### 4. `nginx/nginx.conf` — Reverse Proxy Configuration

Nginx sits in front of the Python backend and handles three types of requests differently:

#### Static Files (CSS, JS for Django Admin)
```nginx
location /static/ {
    alias /app/staticfiles/;
    expires 30d;
    access_log off;
}
```
Nginx serves these directly from disk — **no Python involved**. This is 10–100x faster than making Django serve its own CSS files. `expires 30d` tells browsers to cache these files for 30 days.

#### Media Files (uploaded content)
```nginx
location /media/ {
    alias /app/media/;
    expires 30d;
    access_log off;
}
```
Same concept — direct file serving without hitting Python.

#### Everything Else → Backend
```nginx
location / {
    proxy_pass http://deepfake_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 120s;
}
```

| Header | Why |
|---|---|
| `Host` | Tells Django the original hostname (important for `ALLOWED_HOSTS`) |
| `X-Real-IP` | Preserves the client's real IP address (otherwise Django sees Nginx's IP) |
| `X-Forwarded-For` | Chain of proxy IPs — standard for production setups |
| `proxy_read_timeout 120s` | ML inference can take a few seconds, so Nginx waits up to 120s before timing out |

#### Upload Size Limit
```nginx
client_max_body_size 30M;
```
Allows audio files up to 30 MB to be uploaded. Without this, Nginx rejects large uploads with a `413 Request Entity Too Large` error before they even reach Python.

---

## How the Request Flows Through Docker

```
1. User uploads audio file to http://localhost/api/v1/predict/audio
                                        │
2. Nginx (port 80) receives the request │
   ├── Is it /static/ or /media/?  NO   │
   └── Proxy to backend:8000 ───────────┘
                                        │
3. Gunicorn receives the request        │
   └── Routes to Uvicorn worker ────────┘
                                        │
4. FastAPI handles the request          │
   ├── Validates JWT token              │
   ├── Validates file type/size         │
   ├── Runs preprocessing pipeline      │
   ├── Runs 8 ResNet18 models           │
   ├── Aggregates results               │
   └── Saves to PostgreSQL (via Django ORM)
                                        │
5. Response flows back:                 │
   Backend → Nginx → User              │
```

---

## Docker Commands Reference

```bash
# Build all images and start all containers
docker-compose up --build

# Start in background (detached mode)
docker-compose up --build -d

# View logs of all containers
docker-compose logs -f

# View logs of a specific container
docker-compose logs -f backend

# Stop all containers (data persists in volumes)
docker-compose down

# Stop all containers AND delete all data (volumes)
docker-compose down -v

# Rebuild only the backend (after code changes)
docker-compose up --build backend

# Open a shell inside the backend container
docker exec -it deepfake_backend bash

# Create a Django superuser inside the container
docker exec -it deepfake_backend python manage.py createsuperuser
```

---

## Volume Persistence

| Volume | Purpose | Data survives `down`? | Data survives `down -v`? |
|---|---|---|---|
| `postgres_data` | Database files | ✅ Yes | ❌ No |
| `static_volume` | Django admin CSS/JS | ✅ Yes | ❌ No |
| `media_volume` | Uploaded files | ✅ Yes | ❌ No |
| `./ml/weights` (bind mount) | ML model weights | ✅ Yes | ✅ Yes (on host) |

> ⚠️ **Important:** Running `docker-compose down -v` deletes the PostgreSQL database, including all user accounts and prediction history. Use `docker-compose down` (without `-v`) to preserve data.

---

## Environment Variables

| Variable | Set In | Purpose |
|---|---|---|
| `APP_ENV` | `docker-compose.yml` | `staging` → uses PostgreSQL, `DEBUG=False` |
| `SECRET_KEY` | `docker-compose.yml` | Django's cryptographic signing key (used for JWT) |
| `ALLOWED_HOSTS` | `docker-compose.yml` | Hostnames Django will accept requests from |
| `DATABASE_URL` | `docker-compose.yml` | PostgreSQL connection string |
| `POSTGRES_DB` | `docker-compose.yml` | Database name created on first startup |
| `POSTGRES_USER` | `docker-compose.yml` | Database user created on first startup |
| `POSTGRES_PASSWORD` | `docker-compose.yml` | Database password created on first startup |

> ⚠️ **For production:** Replace the default passwords with strong, unique values. Never use `deepfake_password` in a real deployment.

---

## What Is Explicitly NOT Done in This Step

- No HTTPS / SSL certificates (use a cloud load balancer or Let's Encrypt for production)
- No CI/CD pipeline (GitHub Actions can be added to auto-build and push Docker images)
- No cloud deployment (AWS, GCP, Azure — the Docker setup is cloud-ready but not deployed)
- No Redis / Celery for background jobs
- No container health monitoring (Prometheus, Grafana)

---

## Success Criteria — All Met ✅

- [x] `docker-compose up --build` starts all 3 containers without errors
- [x] `GET http://localhost/api/v1/health` returns `200 OK` via Nginx
- [x] `GET http://localhost/admin/` shows Django admin with CSS loading correctly
- [x] `POST http://localhost/api/v1/predict/audio` runs ML inference successfully
- [x] PostgreSQL stores prediction records persistently
- [x] Data survives `docker-compose down` + `docker-compose up`
