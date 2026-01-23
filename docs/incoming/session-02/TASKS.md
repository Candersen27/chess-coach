# Session 02 Tasks - Backend + Stockfish Integration

## Task Checklist

### 1. Project Setup
- [ ] Create `src/backend/` directory structure
- [ ] Create `requirements.txt` with dependencies:
  ```
  fastapi
  uvicorn[standard]
  python-chess
  ```
- [ ] Create Python virtual environment in project root
- [ ] Install dependencies

---

### 2. Stockfish Engine Wrapper
**File:** `src/backend/engine.py`

- [ ] Create `ChessEngine` class that wraps Stockfish
- [ ] Implement async `analyze(fen, depth)` method
- [ ] Return structured result:
  ```python
  {
      "evaluation": {"type": "cp"|"mate", "value": float|int},
      "best_move": "e2e4",      # UCI format
      "best_move_san": "e4",    # Standard notation
      "depth": 15
  }
  ```
- [ ] Handle mate scores vs centipawn scores
- [ ] Convert UCI move to SAN for display
- [ ] Add error handling for invalid FEN

---

### 3. FastAPI Application
**File:** `src/backend/main.py`

- [ ] Create FastAPI app instance
- [ ] Add CORS middleware (allow all origins for dev)
- [ ] Implement lifespan context manager for engine startup/shutdown
- [ ] Keep engine instance alive between requests

**Endpoints:**

- [ ] `GET /api/health`
  - Returns: `{"status": "ok", "engine": "stockfish"}`

- [ ] `POST /api/analyze`
  - Accepts: `{"fen": "...", "depth": 15}`
  - Validates FEN string
  - Returns analysis result
  - Returns 400 for invalid FEN
  - Returns 500 for engine errors

---

### 4. Frontend Updates
**File:** `src/frontend/chessboard.html`

- [ ] Add "Analyze Position" button to control panel
- [ ] Create `analyzeCurrentPosition()` function:
  - Gets current FEN from display
  - POSTs to `/api/analyze`
  - Handles loading state
  - Displays result
- [ ] Add evaluation display element:
  - Shows "+0.25" format for centipawn
  - Shows "M3" or "M-3" for mate
  - Color code: green for white advantage, red for black
- [ ] Add best move display element
- [ ] Add loading indicator during analysis
- [ ] Handle API errors gracefully

---

### 5. Testing

**Backend tests (manual via curl):**
- [ ] Health endpoint returns 200
- [ ] Starting position analysis works
- [ ] Complex middlegame position works
- [ ] Mate-in-X position returns mate score
- [ ] Invalid FEN returns 400 error

**Frontend tests (manual in browser):**
- [ ] Analyze button triggers request
- [ ] Loading state shows during analysis
- [ ] Evaluation displays correctly
- [ ] Best move displays correctly
- [ ] Error state displays if backend unavailable

**End-to-end:**
- [ ] Load PGN → navigate to position → analyze → see result
- [ ] Make moves → analyze new position → see updated result

---

### 6. Documentation

- [ ] Update `docs/DECISIONS.md` with any new decisions
- [ ] Create `docs/outgoing/session-02/SESSION_SUMMARY.md`
- [ ] Create `docs/outgoing/session-02/README.md`
- [ ] Document any issues encountered

---

## Test Positions

Use these for testing analysis:

```python
TEST_POSITIONS = {
    "starting": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # Expected: ~0.2-0.3 for white
    
    "equal_endgame": "8/5k2/8/8/8/8/5K2/8 w - - 0 1",
    # Expected: 0.0 (dead draw)
    
    "white_winning": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
    # Expected: Large positive (Scholar's mate threat)
    
    "mate_in_one": "k7/8/1K6/8/8/8/8/7R w - - 0 1",
    # Expected: M1
    
    "black_winning": "rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 1",
    # Expected: Large negative (black has mate threat)
}
```

---

## File Structure After Session

```
chess-coach/
├── src/
│   ├── backend/
│   │   ├── main.py
│   │   ├── engine.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── chessboard.html (updated)
│       └── ... (existing files)
├── venv/                    # Python virtual environment
├── docs/
│   ├── incoming/session-02/
│   ├── outgoing/session-02/
│   └── ...
└── ...
```

---

## Potential Blockers

1. **Stockfish path:** Use `/usr/games/stockfish` (verified installed)
2. **CORS issues:** Make sure middleware is added before routes
3. **Async engine:** Use `chess.engine.popen_uci` with `await`
4. **Port conflicts:** Default to 8000, can change if needed

---

## Notes for Claude Code

- Reference `docs/outgoing/session-01/STOCKFISH_INTEGRATION_GUIDE.md` for code examples
- Keep the engine wrapper simple—complexity can be added later
- Evaluation display doesn't need to be pretty, just functional
- Commit changes before ending session
