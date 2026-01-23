# Session 02 Documentation - Backend + Stockfish Integration

**Quick Navigation:**
- [Session Summary](SESSION_SUMMARY.md) - Complete session report
- [Backend Code](../../src/backend/) - FastAPI application and engine wrapper
- [Frontend Updates](../../src/frontend/chessboard.html) - Analysis UI

---

## Overview

This session implemented a complete FastAPI backend with Stockfish integration and updated the frontend to display position analysis.

**Key Features:**
- ✅ FastAPI REST API with health check and analysis endpoints
- ✅ Async Stockfish engine wrapper
- ✅ Position analysis with evaluation and best move
- ✅ Frontend UI for triggering analysis
- ✅ Color-coded evaluation display
- ✅ Mate-in-X detection

---

## Quick Start

### 1. Start Backend

```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

**API Docs:** http://localhost:8000/docs (FastAPI auto-generated)

### 2. Open Frontend

Open [src/frontend/chessboard.html](../../src/frontend/chessboard.html) in your browser.

### 3. Test Analysis

1. Set up a position (or use starting position)
2. Click "Analyze Position" button
3. View evaluation and best move

---

## API Reference

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "engine": "stockfish"
}
```

### POST /api/analyze

Analyze a chess position.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15
}
```

**Response:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "evaluation": {
    "type": "cp",
    "value": 0.35
  },
  "best_move": "e2e4",
  "best_move_san": "e4",
  "depth": 15
}
```

**Evaluation Types:**
- `"cp"` - Centipawn evaluation (in pawn units, e.g., 0.35 = +35 centipawns)
- `"mate"` - Forced mate (value = moves to mate)

**Error Responses:**
- `400` - Invalid FEN string
- `500` - Engine error

---

## Code Structure

### Backend

**[src/backend/main.py](../../src/backend/main.py)** - FastAPI Application
- FastAPI app initialization
- CORS middleware configuration
- Lifespan management for engine
- Health and analyze endpoints
- Request/response models

**[src/backend/engine.py](../../src/backend/engine.py)** - Engine Wrapper
- `ChessEngine` class
- Async Stockfish initialization
- Position analysis method
- Score conversion (centipawns → pawns)
- UCI to SAN move conversion

**[src/backend/requirements.txt](../../src/backend/requirements.txt)** - Dependencies
- fastapi
- uvicorn[standard]
- python-chess

### Frontend

**[src/frontend/chessboard.html](../../src/frontend/chessboard.html)** - Updated UI
- Analysis button in controls
- Analysis panel for displaying results
- Color-coded evaluation display
- Best move display
- Error handling

**Key Functions:**
- `analyzeCurrentPosition()` - Calls API and handles response
- `displayAnalysis(data)` - Formats and displays analysis results

---

## Implementation Details

### Async Engine Management

The engine is initialized once at startup and kept alive between requests:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize engine
    await chess_engine.start()
    yield
    # Shutdown: Clean up engine
    await chess_engine.stop()

app = FastAPI(lifespan=lifespan)
```

### Evaluation Formatting

Frontend formats evaluations based on type:

**Centipawn:**
- Positive: "+0.42" (green) - White advantage
- Negative: "-0.35" (red) - Black advantage
- Zero: "0.00" (gray) - Equal position

**Mate:**
- Positive: "M3" (green) - Mate in 3 for side to move
- Negative: "M-2" (red) - Mated in 2 moves

### CORS Configuration

Development configuration allows all origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **Production:** Restrict `allow_origins` to specific domains

---

## Testing

### Manual Backend Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Analyze starting position
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'

# Test mate-in-one
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "k7/8/1K6/8/8/8/8/7R w - - 0 1"}'

# Test invalid FEN
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "invalid-fen"}'
```

### Manual Frontend Testing

1. **Load PGN Test:**
   - Load a PGN file
   - Navigate to different positions
   - Click "Analyze Position" for each
   - Verify evaluations change appropriately

2. **Make Moves Test:**
   - Make moves on the board
   - Analyze after each move
   - Verify evaluation updates

3. **Error Handling Test:**
   - Stop backend server
   - Click "Analyze Position"
   - Verify error message displays

---

## Troubleshooting

### Backend won't start

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Activate virtual environment and install dependencies
```bash
source venv/bin/activate
pip install -r src/backend/requirements.txt
```

### CORS errors in browser

**Problem:** `Access-Control-Allow-Origin` error in browser console

**Solution:** Verify CORS middleware is configured in main.py

### Analysis returns error

**Problem:** "Engine not started" error

**Solution:** Check Stockfish is installed at `/usr/games/stockfish`
```bash
which stockfish
# If not at /usr/games/stockfish, update engine_path in engine.py
```

### Frontend can't connect to backend

**Problem:** "Failed to fetch" or network error

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check API_BASE_URL in chessboard.html matches backend port
3. Verify no firewall blocking localhost:8000

---

## Performance Notes

- **Analysis Time:** ~1-2 seconds at depth 15
- **Engine Startup:** ~0.1 seconds (one-time at server start)
- **Memory:** ~50MB for backend + engine
- **Concurrent Requests:** Handled sequentially by single engine instance

**Optimization Ideas for Future:**
- Multiple engine instances for parallel analysis
- Caching common positions
- Adjustable depth based on position complexity

---

## Session Artifacts

**Created Files:**
- src/backend/main.py
- src/backend/engine.py
- src/backend/requirements.txt

**Modified Files:**
- src/frontend/chessboard.html

**Created Directories:**
- venv/ (Python virtual environment)
- src/backend/

**Documentation:**
- docs/outgoing/session-02/SESSION_SUMMARY.md
- docs/outgoing/session-02/README.md (this file)

---

## Related Documentation

- [Session 01 Documentation](../session-01/) - Frontend chessboard implementation
- [Stockfish Integration Guide](../session-01/STOCKFISH_INTEGRATION_GUIDE.md) - Detailed Stockfish usage
- [Architecture Overview](../session-01/ARCHITECTURE_OVERVIEW.md) - Project structure

---

## Future Enhancements

**Session 03 Preview:**
- Play against Stockfish
- Difficulty levels (ELO calibration)
- Move suggestions during play

**Session 04 Preview:**
- Analyze entire games
- Move-by-move evaluation graph
- Blunder detection

**Session 05 Preview:**
- Save games to database
- User accounts
- Game history and statistics
