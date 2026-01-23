# Session 02 Context - Backend + Stockfish Integration

> **Date:** January 23, 2025
> **Phase:** Phase 1 - Technical Foundation
> **Session Goal:** Build FastAPI backend with Stockfish analysis endpoint

---

## What Exists (Session 01 Complete)

### Frontend
- `src/frontend/chessboard.html` — Fully functional interactive chessboard
- PGN loading, move navigation, keyboard shortcuts
- Programmatic API: `chessBoard.setPosition()`, `chessBoard.makeMove()`, `chessBoard.loadPGN()`
- Piece images stored locally in `src/frontend/img/chesspieces/wikipedia/`

### Infrastructure
- WSL (Ubuntu) development environment
- Stockfish installed: `/usr/games/stockfish`
- Git repo initialized and pushed to GitHub

### Documentation
- `docs/outgoing/session-01/` — Complete session 01 docs including:
  - STOCKFISH_INTEGRATION_GUIDE.md (has FastAPI code examples)
  - API_REFERENCE.md (frontend JavaScript API)
  - ARCHITECTURE_OVERVIEW.md

---

## What We're Building This Session

### Backend API (FastAPI)

```
src/backend/
├── main.py              # FastAPI app, CORS, lifespan management
├── engine.py            # Stockfish wrapper class
└── requirements.txt     # Dependencies
```

### Endpoints

**GET /api/health**
```json
{"status": "ok", "engine": "stockfish"}
```

**POST /api/analyze**
Request:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15
}
```

Response:
```json
{
  "fen": "...",
  "evaluation": {
    "type": "cp",
    "value": 0.25
  },
  "best_move": "e2e4",
  "best_move_san": "e4",
  "depth": 15
}
```

### Frontend Updates
- Add "Analyze Position" button to chessboard.html
- Display evaluation next to board (e.g., "+0.25" or "M3")
- Display best move suggestion
- Loading state while analysis runs

---

## Technical Decisions (Pre-Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | FastAPI | Async support, auto OpenAPI docs, scales better |
| Frontend serving | Separate | Faster dev iteration, combine later for deploy |
| Analysis depth | 15 (default) | Balance of speed (~1-2s) and quality |
| Engine management | Keep alive | Reuse engine instance between requests |

---

## Key Implementation Notes

### Stockfish in python-chess

```python
import chess
import chess.engine

# Async version for FastAPI
engine = await chess.engine.popen_uci("/usr/games/stockfish")
info = await engine.analyse(board, chess.engine.Limit(depth=15))
await engine.quit()
```

### CORS Required
Frontend runs from `file://` or different port. Enable CORS:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Evaluation Types
- Centipawn (cp): `{"type": "cp", "value": 0.25}` — White up 0.25 pawns
- Mate: `{"type": "mate", "value": 3}` — Mate in 3 moves

---

## Out of Scope (Future Sessions)

- Full game analysis (all moves) — Session 04
- Playing against Stockfish — Session 03
- Database/persistence — Session 05
- ELO calibration for Stockfish — Session 03

---

## Commands Reference

```bash
# Navigate to project
cd ~/myCodes/projects/chess-coach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (after requirements.txt exists)
pip install -r src/backend/requirements.txt

# Run FastAPI server
cd src/backend
uvicorn main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'
```

---

## Success Criteria

1. `GET /api/health` returns 200
2. `POST /api/analyze` returns valid evaluation for starting position
3. Frontend "Analyze" button triggers analysis and displays result
4. End-to-end test: make moves on board → click analyze → see evaluation

---

## Reference Files

- `docs/outgoing/session-01/STOCKFISH_INTEGRATION_GUIDE.md` — FastAPI code examples
- `docs/outgoing/session-01/API_REFERENCE.md` — Frontend JS API
- `src/frontend/chessboard.html` — Current frontend implementation
