# Use the official Python 3.10 slim image as the base
FROM python:3.10-slim

# Set environment variables to ensure Python output is logged and no pyc files are created
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system-level dependencies required for PostgreSQL and Audio Processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements first to cache the pip install step
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose the port Uvicorn/Gunicorn will listen on
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
