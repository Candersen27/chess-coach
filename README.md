# Chess Coach

An AI-powered chess coaching platform that lets you analyze games with Stockfish, play against an adjustable-difficulty opponent, and have coaching conversations with Claude (engine analysis + LLM explanation via native tool calling).

## Quick Start

### Run locally (Python)

```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

Then open **http://localhost:8000/** — the backend serves the frontend, so there's no separate HTML file to open.

> Optional: set `ANTHROPIC_API_KEY` in `.env` to enable Claude chat coaching. Without it, all Stockfish features still work.

### Run with Docker

```bash
docker build -t chess-coach .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$YOUR_KEY chess-coach
# open http://localhost:8000/
```

### Use It

- **Load a PGN:** Click "Load PGN" to analyze an existing game
- **Navigate moves:** Use arrow keys or the navigation buttons
- **Analyze position:** Click "Analyze Position" for Stockfish evaluation
- **Analyze full game:** Click "Analyze Full Game" for move-by-move analysis with accuracy stats
- **Play vs Coach:** Select ELO level and start a new game as White or Black
- **Chat coaching:** Talk to the Claude-powered coach, who can control the board and reference chess literature (requires an API key — see below)

## Deployment

The app deploys as a single Docker container to **Fly.io** (Stockfish runs as a subprocess, so serverless platforms don't work).

```bash
fly launch --no-deploy             # generates fly.toml from the Dockerfile
# in fly.toml: internal_port = 8000, [[vm]] memory = 1024
fly secrets set ANTHROPIC_API_KEY=$YOUR_KEY
fly secrets set PER_IP_TOKEN_CAP=150000 DAILY_TOKEN_CAP=1000000
fly deploy
fly secrets set ALLOWED_ORIGINS=https://your-app.fly.dev   # lock down CORS once live
```

### API cost protection

Public visitors use Claude coaching on the server's key up to a **per-IP daily token budget** (shown as a live meter in the chat panel, with warnings at 35% and 10% remaining). When the budget is exhausted, visitors can paste **their own Anthropic API key** (BYOK) to continue — it's stored in their browser and bypasses the cap. Caps are tuned via `PER_IP_TOKEN_CAP` / `DAILY_TOKEN_CAP`.

## Documentation

- **[PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md)** - Deep dive into how everything works, why we made the decisions we did, and lessons learned. Start here for a comprehensive understanding.

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System diagrams and component overview

- **[docs/DECISIONS.md](docs/DECISIONS.md)** - Architecture decision log with rationale

- **[docs/PROGRESS.md](docs/PROGRESS.md)** - Session-by-session development history

## Features

- Interactive chessboard with PGN loading and navigation
- Single position analysis with Stockfish
- Full game analysis with accuracy percentages and move classification
- Multi-game batch analysis with tactical pattern detection and phase performance
- Play vs Coach mode with ELO-adjustable opponent (1350-2800)
- Claude chat coaching with native tool calling (board control), book integration (Capablanca's *Chess Fundamentals*), and prompt caching
- PGN export (plain and annotated)

## Coming Soon

- Database for player profiles and game history
- Streaming chat responses and multi-turn tool-calling loops
- Mobile-responsive layout
- Additional coaching books

## Tech Stack

- **Frontend:** HTML/CSS/JavaScript with chessboard.js + chess.js (served by the backend as static files)
- **Backend:** Python FastAPI + python-chess
- **Engine:** Stockfish
- **AI:** Anthropic Claude (tool calling + prompt caching)
- **Deploy:** Docker → Fly.io

## API

Interactive documentation available at http://localhost:8000/docs when the server is running.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Server status |
| `/api/analyze` | POST | Single position analysis |
| `/api/move` | POST | Get engine move at ELO |
| `/api/game/analyze` | POST | Full game analysis |
| `/api/games/analyze-batch` | POST | Multi-game batch analysis + patterns |
| `/api/chat` | POST | Claude chat coaching (board control via tools) |
| `/api/coach/move` | POST | Coaching feedback on a move (Stockfish + Claude) |
| `/api/budget` | GET | Per-IP demo token budget status |
| `/api/books` | GET | Available coaching books |
