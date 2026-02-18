# Getting Started with Chess Coach

## Prerequisites

1. **Python 3.10+** installed
2. **Stockfish** chess engine installed at `/usr/games/stockfish`
   ```bash
   sudo apt install stockfish
   ```
3. **Anthropic API key** for the Claude-powered coaching features

## Setup

### 1. Create and activate the virtual environment

```bash
cd /home/thcth/myCodes/projects/chess-coach
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r src/backend/requirements.txt
```

### 3. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Or create a `.env` file in `src/backend/` with:

```
ANTHROPIC_API_KEY=your-key-here
```

## Running the App

### Start the backend server

```bash
source venv/bin/activate
cd src/backend
uvicorn main:app --port 8000
```

You should see:
```
Chess engine started successfully
Chess coach initialized successfully
```

### Open the frontend

Open `src/frontend/chessboard.html` in your browser. The frontend connects to the backend at `http://localhost:8000`.

## Verify it's working

Hit the health check endpoint:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status": "ok", "engine": "stockfish"}
```

## Notes

- The backend must be running for the frontend to function (analysis, chat, coaching all require it).
- If the API key is missing, the server still starts but coaching/chat endpoints return 503.
- Stockfish must be installed at `/usr/games/stockfish` (the default `apt install` location).
