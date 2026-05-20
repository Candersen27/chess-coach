# Chess Coach — production image
# Single FastAPI service that serves the frontend (StaticFiles) and spawns
# Stockfish as a subprocess. Serverless platforms can't run the subprocess,
# which is why we ship a real container.
FROM python:3.12-slim

# Stockfish installs to /usr/games/stockfish on Debian — matches the default
# STOCKFISH_PATH the backend falls back to.
RUN apt-get update \
    && apt-get install -y --no-install-recommends stockfish \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first so the layer caches when only source changes.
COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --no-cache-dir -r src/backend/requirements.txt

# Source + book data. The book loader reads <root>/data/books/ at runtime,
# so the src/ + data/ layout must be preserved.
COPY src/ ./src/
COPY data/ ./data/

# Run as non-root.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV STOCKFISH_PATH=/usr/games/stockfish \
    PYTHONUNBUFFERED=1

EXPOSE 8000
WORKDIR /app/src/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
