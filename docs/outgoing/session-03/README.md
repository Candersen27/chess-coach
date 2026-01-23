# Session 03 Documentation - Documentation Cleanup + Play vs Coach

**Quick Navigation:**
- [Session Summary](SESSION_SUMMARY.md) - Complete session report
- [Backend Code](../../src/backend/) - engine.py and main.py updates
- [Frontend Code](../../src/frontend/chessboard.html) - Play mode UI

---

## Overview

Two-part session:
- **Part A:** Reorganized project documentation structure
- **Part B:** Built play-vs-coach mode with ELO-calibrated Stockfish

---

## Quick Start - Play vs Coach

### 1. Start Backend

```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

### 2. Open Frontend

Open `src/frontend/chessboard.html` in browser

### 3. Play a Game

1. Find "Play vs Coach" panel (blue background)
2. Select coach strength (default: Intermediate 1500)
3. Click "New Game as White" or "New Game as Black"
4. Drag pieces to make moves
5. Coach responds automatically
6. Game ends with result display

---

## API Reference

### New Endpoint: POST /api/move

Get engine's move for a position at specified ELO.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "elo": 1500
}
```

**Parameters:**
- `fen` (string, required) - FEN string of current position
- `elo` (integer, optional) - Engine strength 1350-2800, default 1500

**Response:**
```json
{
  "move": "e2e4",
  "move_san": "e4",
  "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
}
```

**Errors:**
- `400` - Invalid FEN or game already over
- `500` - Engine error

---

## ELO Strength Levels

| Level | ELO | Plays Like |
|-------|-----|------------|
| Beginner | 1350 | Beginner mistakes |
| Intermediate | 1500 | Casual player |
| Advanced | 1700 | Club player |
| Strong | 1900 | Tournament player |
| Expert | 2100 | Expert |
| Master | 2300 | Chess master |
| Grandmaster | 2500 | Top GM |
| Maximum | 2800 | Peak strength |

**Note:** Range is 1350-2800 based on installed Stockfish version. Not all Stockfish builds support 800-1350.

---

## Code Structure

### Backend Changes

**[src/backend/engine.py](../../src/backend/engine.py:101)**

New method:
```python
async def get_move(self, fen: str, elo: int = 1500) -> Dict[str, Any]:
    """Get engine's move at specified ELO level."""
    # Configure strength
    await self.engine.configure({
        "UCI_LimitStrength": True,
        "UCI_Elo": max(1350, min(2800, elo))
    })

    # Get move
    result = await self.engine.play(board, chess.engine.Limit(time=1.0))

    return {
        "move": result.move.uci(),
        "move_san": board.san(result.move),
        "fen_after": board_after.fen()
    }
```

**[src/backend/main.py](../../src/backend/main.py:76)**

New endpoint:
```python
@app.post("/api/move", response_model=MoveResponse)
async def get_engine_move(request: MoveRequest):
    result = await chess_engine.get_move(request.fen, request.elo)
    return result
```

### Frontend Changes

**[src/frontend/chessboard.html](../../src/frontend/chessboard.html)**

**New UI:**
- Play vs Coach panel
- ELO selector dropdown
- New Game buttons
- Status display

**New Functions:**
- `startGameAsWhite()` / `startGameAsBlack()`
- `requestCoachMove()` - Fetches move from API
- `onDropPiece()` - Handles player moves
- `checkGameOver()` - Detects game end
- `updateGameStatus()` - Updates UI

**Game State:**
```javascript
let isPlaying = false;      // Play mode active?
let playerColor = null;     // 'white' or 'black'
let isPlayerTurn = false;   // Player's turn?
```

---

## Game Flow

```
User clicks "New Game as White"
  ↓
Board resets, isPlaying = true, isPlayerTurn = true
  ↓
Player drags piece (onDropPiece called)
  ↓
Move validated and applied
  ↓
Check game over? → If yes, end game
  ↓
If no, requestCoachMove()
  ↓
POST /api/move with FEN and ELO
  ↓
Apply coach's move
  ↓
Check game over? → If yes, end game
  ↓
If no, isPlayerTurn = true, repeat
```

---

## Testing

### Manual Backend Tests

```bash
# Test starting position, ELO 1500
curl -X POST http://localhost:8000/api/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "elo": 1500}'

# Test with high ELO
curl -X POST http://localhost:8000/api/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "elo": 2500}'

# Test game over position (should error)
curl -X POST http://localhost:8000/api/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"}'
```

### Frontend Tests

1. **Play as White:**
   - Select ELO, click "New Game as White"
   - Make opening move (e.g., e4)
   - Verify coach responds
   - Verify status updates

2. **Play as Black:**
   - Click "New Game as Black"
   - Verify coach moves first
   - Make response move
   - Continue game

3. **ELO Variation:**
   - Play at 1350 - coach makes weaker moves
   - Play at 2500 - coach plays stronger
   - Verify different play styles

4. **Game End:**
   - Play to checkmate
   - Verify "Checkmate! [Color] wins!" message
   - Verify cannot move after game over

---

## Troubleshooting

### "Engine ELO too low" Error

**Problem:** Requesting ELO below 1350

**Solution:** Stockfish minimum is 1350. Use values 1350-2800.

### Coach Not Responding

**Problem:** Frontend shows "Coach thinking..." forever

**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check browser console for errors
3. Verify CORS is enabled in backend

### Game Over Not Detected

**Problem:** Game continues after checkmate

**Solution:** Ensure latest chessboard.html with `checkGameOver()` function.

### Cannot Move Pieces

**Problem:** Pieces snap back

**Solution:**
- Check it's your turn (status should say "Your turn")
- Verify playing correct color
- Ensure play mode is active (clicked "New Game")

---

## Documentation Updates (Part A)

### Created Files

1. **[docs/DECISIONS.md](../../DECISIONS.md)**
   - 10 decisions total (DECISION-001 through DECISION-010)
   - Includes Session 02 and Session 03 decisions

2. **[docs/PROGRESS.md](../../PROGRESS.md)**
   - Sessions 0, 1, 2, 3 logged
   - What worked, what didn't, key learnings

3. **[docs/ARCHITECTURE.md](../../ARCHITECTURE.md)**
   - System overview
   - Updated for current state (backend exists, play mode added)

### Structure

```
docs/
├── DECISIONS.md              # Project-wide decisions
├── PROGRESS.md               # Session summaries
├── ARCHITECTURE.md           # System architecture
├── incoming/                 # Session input docs
│   ├── session-01/
│   ├── session-02/
│   └── session-03/
└── outgoing/                 # Session output docs
    ├── session-01/
    ├── session-02/
    └── session-03/
```

---

## New Architectural Decisions

### [DECISION-009] ELO Range 1350-2800
- Stockfish minimum UCI_Elo varies by version
- This build: 1350-2800
- Documented actual range, not theoretical

### [DECISION-010] Frontend Manages Game State
- Backend stateless (no sessions)
- Frontend tracks: position, turn, color
- Games lost on refresh (acceptable for MVP)
- May add persistence later

---

## Performance Notes

- **Coach move time:** ~1 second (configured time limit)
- **API response:** ~1-2 seconds total (including network)
- **UI delay:** 500ms before requesting coach move (feels natural)
- **No noticeable lag:** Single-engine handles requests sequentially

---

## Future Enhancements

**Immediate Opportunities:**
- Save/load games
- Adjustable time controls
- Hint system (show best move)
- Undo move

**Phase 2:**
- Full game analysis mode
- Opening book suggestions
- Tactical puzzle generator
- Game database

---

## Related Files

- [Session 03 Summary](SESSION_SUMMARY.md) - Detailed session report
- [Session 02 Summary](../session-02/SESSION_SUMMARY.md) - Previous session
- [DECISIONS.md](../../DECISIONS.md) - All architectural decisions
- [PROGRESS.md](../../PROGRESS.md) - All session summaries
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture

---

*Play vs Coach mode successfully implemented with clean, maintainable code and comprehensive documentation.*
