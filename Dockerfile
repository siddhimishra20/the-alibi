# Multi-stage Dockerfile for THE ALIBI
FROM python:3.11-slim

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=http://host.docker.internal:11434

WORKDIR /app

# Install system dependencies (build-essential, curl, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn

# Copy project source
COPY . .

# Ensure audio assets exist
RUN python -c "from alibi.audio.manager import ensure_all_audio_assets; ensure_all_audio_assets('assets/audio')"

# Expose web server port
EXPOSE 8000

# Default command: launch the FastAPI Web Application (dynamic cloud $PORT support)
CMD ["sh", "-c", "python run.py --web --host 0.0.0.0 --port ${PORT:-8000}"]

