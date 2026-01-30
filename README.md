# Chess Coach

An AI-powered chess coaching platform that lets you analyze games with Stockfish, play against an adjustable-difficulty opponent, and (soon) have coaching conversations with Claude.

## Quick Start

### Start the Backend

```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

### Open the Frontend

Open `src/frontend/chessboard.html` in your browser.

### Use It

- **Load a PGN:** Click "Load PGN" to analyze an existing game
- **Navigate moves:** Use arrow keys or the navigation buttons
- **Analyze position:** Click "Analyze Position" for Stockfish evaluation
- **Analyze full game:** Click "Analyze Full Game" for move-by-move analysis with accuracy stats
- **Play vs Coach:** Select ELO level and start a new game as White or Black

## Documentation

- **[PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md)** - Deep dive into how everything works, why we made the decisions we did, and lessons learned. Start here for a comprehensive understanding.

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System diagrams and component overview

- **[docs/DECISIONS.md](docs/DECISIONS.md)** - Architecture decision log with rationale

- **[docs/PROGRESS.md](docs/PROGRESS.md)** - Session-by-session development history

## Current Features (Phase 1)

- Interactive chessboard with PGN loading and navigation
- Single position analysis with Stockfish
- Full game analysis with accuracy percentages and move classification
- Play vs Coach mode with ELO-adjustable opponent (1350-2800)
- PGN export (plain and annotated)

## Coming Soon

- **Phase 2:** Database for player profiles and game history
- **Phase 3:** Claude API integration for natural language coaching
- **Phase 4:** RAG system for chess literature references

## Tech Stack

- **Frontend:** HTML/CSS/JavaScript with chessboard.js + chess.js
- **Backend:** Python FastAPI + python-chess
- **Engine:** Stockfish
- **Environment:** WSL (Ubuntu)

## API

Interactive documentation available at http://localhost:8000/docs when the server is running.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Server status |
| `/api/analyze` | POST | Single position analysis |
| `/api/move` | POST | Get engine move at ELO |
| `/api/game/analyze` | POST | Full game analysis |
