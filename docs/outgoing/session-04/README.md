# Session 04 Documentation - Game Analysis & PGN Export

**Quick Navigation:**
- [Session Summary](SESSION_SUMMARY.md) - Complete session report
- [Backend Code](../../src/backend/) - engine.py and main.py updates
- [Frontend Code](../../src/frontend/chessboard.html) - Analysis UI and export functions

---

## Overview

Added comprehensive game analysis capabilities:
- Move-by-move evaluation and classification
- Accuracy percentage calculation
- Color-coded move display
- PGN export (plain and annotated)

---

## Quick Start - Analyze a Game

### 1. Start Backend

```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

### 2. Open Frontend

Open `src/frontend/chessboard.html` in browser

### 3. Analyze a Game

1. Load a PGN file (or play a game vs coach)
2. Click "Analyze Full Game" button
3. Wait for analysis to complete (~2-5 minutes for 40-move game)
4. Review color-coded move list and accuracy percentages
5. Click any move to jump to that position
6. Export annotated PGN for further study

---

## API Reference

### POST /api/game/analyze

Analyze all moves in a complete game.

**Request:**
```json
{
  "pgn": "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6...",
  "depth": 15
}
```

**Parameters:**
- `pgn` (string, required) - PGN string of the game
- `depth` (integer, optional) - Analysis depth 1-30, default 15

**Response:**
```json
{
  "moves": [
    {
      "move_number": 1,
      "color": "white",
      "move_san": "e4",
      "move_uci": "e2e4",
      "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
      "eval_before": 0.37,
      "eval_after": 0.25,
      "eval_change": -0.12,
      "best_move_san": "e4",
      "best_move_uci": "e2e4",
      "classification": "excellent"
    }
  ],
  "summary": {
    "total_moves": 48,
    "white_accuracy": 85.2,
    "black_accuracy": 78.4,
    "white_blunders": 1,
    "white_mistakes": 2,
    "white_inaccuracies": 3,
    "black_blunders": 2,
    "black_mistakes": 3,
    "black_inaccuracies": 4,
    "critical_moments": [12, 23, 35]
  }
}
```

**Errors:**
- `400` - Invalid PGN
- `500` - Engine error

**Performance:** ~2-4 seconds per position at depth 15

---

## Move Classification

Based on centipawn loss from moving player's perspective:

| Classification | CP Loss | Color | Symbol |
|----------------|---------|-------|--------|
| Excellent | ≤ 0 | Green | ! |
| Good | 0-20 | Dark Green | - |
| Inaccuracy | 20-50 | Yellow | ?! |
| Mistake | 50-100 | Orange | ? |
| Blunder | > 100 | Red | ?? |

---

## Accuracy Calculation

**Formula:**
```
accuracy = max(0, min(100, 100 - (average_centipawn_loss / 2)))
```

**Examples:**
- 0 CP avg loss → 100% accuracy
- 20 CP avg loss → 90% accuracy
- 50 CP avg loss → 75% accuracy
- 100 CP avg loss → 50% accuracy

**Note:** This is a simplified formula for MVP. Differs from Chess.com's exponential formula but provides consistent, predictable feedback.

---

## Code Structure

### Backend Changes

**[src/backend/engine.py](../../src/backend/engine.py)**

New imports:
```python
import chess.pgn
import io
from typing import List
```

New functions:
```python
def classify_move(cp_loss: float) -> str:
    """Classify move: excellent, good, inaccuracy, mistake, or blunder"""

def calculate_accuracy(cp_losses: List[float]) -> float:
    """Calculate accuracy percentage from CP losses"""
```

New method:
```python
async def analyze_game(self, pgn: str, depth: int = 15) -> Dict[str, Any]:
    """Analyze all moves in a PGN game.

    Returns:
        {
            "moves": [...],  # List of MoveAnalysis
            "summary": {...}  # GameSummary
        }
    """
```

**[src/backend/main.py](../../src/backend/main.py)**

New models:
```python
class GameAnalysisRequest(BaseModel):
    pgn: str
    depth: int = 15

class MoveAnalysis(BaseModel):
    move_number: int
    color: str
    move_san: str
    move_uci: str
    fen_before: str
    fen_after: str
    eval_before: Optional[float]
    eval_after: Optional[float]
    eval_change: Optional[float]
    best_move_san: str
    best_move_uci: str
    classification: str

class GameSummary(BaseModel):
    total_moves: int
    white_accuracy: float
    black_accuracy: float
    white_blunders: int
    white_mistakes: int
    white_inaccuracies: int
    black_blunders: int
    black_mistakes: int
    black_inaccuracies: int
    critical_moments: List[int]

class GameAnalysisResponse(BaseModel):
    moves: List[MoveAnalysis]
    summary: GameSummary
```

New endpoint:
```python
@app.post("/api/game/analyze", response_model=GameAnalysisResponse)
async def analyze_game(request: GameAnalysisRequest):
    """Analyze all moves in a complete game."""
```

### Frontend Changes

**[src/frontend/chessboard.html](../../src/frontend/chessboard.html)**

**New CSS:** Game analysis panel styling, color-coded move items

**New HTML:**
```html
<div id="gameAnalysisPanel" class="game-analysis-panel">
    <h3>Game Analysis</h3>
    <button onclick="analyzeFullGame()">Analyze Full Game</button>
    <div id="analysisResults">
        <div class="accuracy-display">...</div>
        <div class="moves-list">...</div>
        <div class="export-buttons">...</div>
    </div>
    <div id="loadingAnalysis">Analyzing game...</div>
</div>
```

**New Functions:**
- `analyzeFullGame()` - Fetches analysis from API
- `displayGameAnalysis(data)` - Renders results in UI
- `exportPlainPGN()` - Downloads plain PGN
- `exportAnnotatedPGN()` - Downloads annotated PGN with evaluations
- `generateAnnotatedPGN(moves)` - Builds PGN with comments
- `downloadPGN(content, filename)` - Triggers browser download

---

## Testing

### Backend Tests

```bash
# Test short game
curl -X POST http://localhost:8000/api/game/analyze \
  -H "Content-Type: application/json" \
  -d '{"pgn": "1. d4 d5 2. Bf4 Nf6 3. Nf3", "depth": 12}'

# Test with sample PGN file
PGN=$(cat data/samples/Chrandersen_vs_magedoooo_2025.09.29.pgn)
curl -X POST http://localhost:8000/api/game/analyze \
  -H "Content-Type: application/json" \
  -d "{\"pgn\": \"$PGN\", \"depth\": 15}"
```

### Frontend Tests

1. **Load and Analyze:**
   - Load PGN file
   - Click "Analyze Full Game"
   - Verify loading indicator appears
   - Verify results display correctly

2. **Move List:**
   - Verify color coding matches classifications
   - Click moves to verify board updates
   - Hover for tooltips on mistakes/blunders

3. **Accuracy Display:**
   - Verify White and Black accuracy percentages
   - Verify mistake counts (blunders, mistakes, inaccuracies)

4. **Export:**
   - Export plain PGN, verify file downloads
   - Export annotated PGN, verify evaluations included
   - Open exported PGN in Chess.com or Lichess

---

## PGN Export Formats

### Plain PGN
Standard PGN with just the moves:
```
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6...
```

### Annotated PGN
PGN with symbols and evaluations:
```
1. e4! {+0.25} e5 {+0.25} 2. Nf3 {+0.37} Nc6 {+0.32}
3. Bb5?! {inaccuracy. +0.37 → +0.15. Best: d4} {+0.15}
a6 {+0.15} 4. Ba4? {mistake. +0.15 → -0.35. Best: Bxc6} {-0.35}...
```

**Symbols:**
- `!!` - Brilliant move
- `!` - Excellent move
- `?!` - Inaccuracy
- `?` - Mistake
- `??` - Blunder

**Comments:**
- All moves: `{evaluation}`
- Bad moves: `{classification. eval_before → eval_after. Best: move}`

---

## Performance Considerations

### Analysis Speed

**Factors:**
- Number of moves (linear time)
- Analysis depth (exponential time)
- Position complexity (varies)

**Typical Times (depth 15):**
- 10-move game: ~30-40 seconds
- 25-move game: ~1-2 minutes
- 40-move game: ~2-5 minutes
- 60-move game: ~4-8 minutes

**Optimization Options:**
1. Lower depth for game analysis (depth 12 → 50% faster)
2. Add progress indicator
3. Analyze specific move ranges only
4. Cache results in browser localStorage

### Memory Usage

- Stockfish: ~50-100MB per instance
- Frontend: ~10-20MB for analysis data
- No memory leaks observed in testing

---

## Troubleshooting

### "No game loaded" Error

**Problem:** Clicking "Analyze Full Game" shows error

**Solution:**
1. Load a PGN file first, or
2. Play a game vs coach, or
3. Make some moves on the board

### Analysis Takes Forever

**Problem:** Analysis doesn't complete

**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check browser console for errors
3. Verify game is valid (not stuck in loading state)
4. Try shorter game first to verify system works

### Export Downloads Empty File

**Problem:** Exported PGN is empty

**Solution:**
1. Verify game is loaded (move list visible)
2. For annotated export, analyze game first
3. Check browser console for JavaScript errors

### Color Coding Not Showing

**Problem:** All moves look the same color

**Solution:**
1. Refresh page to reload CSS
2. Check analysis actually ran (should see accuracy percentages)
3. Try different browser (CSS compatibility)

---

## Advanced Usage

### Custom Analysis Depth

Edit `analyzeFullGame()` function to use different depth:

```javascript
body: JSON.stringify({
    pgn: pgn,
    depth: 12  // Faster but less accurate
})
```

### Filter Moves by Classification

Add filter to move list:

```javascript
const blundersOnly = data.moves.filter(m => m.classification === 'blunder');
```

### Compare Multiple Games

Store analysis results:

```javascript
const gameHistory = [];
gameHistory.push({
    pgn: pgn,
    analysis: currentGameAnalysis,
    date: new Date()
});
```

---

## Future Enhancements

**Planned for Next Sessions:**
- Progress indicator ("Analyzing move X of Y...")
- Partial game analysis (specify move range)
- Opening book integration (mark book moves)
- Claude API integration (natural language explanations)

**Backlog Items:**
- Analysis result caching
- Comparative game analysis
- Training puzzle generation from blunders
- Position theme detection (tactical motifs)

---

## New Architectural Decisions

### [DECISION-011] Move Classification Thresholds

**Decision:** Use 0/20/50/100 CP thresholds (Chess.com standard)
**Rationale:** Well-understood, consistent across platforms
**See:** [docs/DECISIONS.md](../../DECISIONS.md#decision-011-move-classification-thresholds)

### [DECISION-012] Simplified Accuracy Formula

**Decision:** Linear formula `100 - (avg_cp_loss / 2)`
**Rationale:** Simple, predictable, good enough for MVP
**See:** [docs/DECISIONS.md](../../DECISIONS.md#decision-012-simplified-accuracy-formula)

---

## Related Files

- [Session Summary](SESSION_SUMMARY.md) - Detailed session report
- [Session 03 Summary](../session-03/SESSION_SUMMARY.md) - Previous session
- [DECISIONS.md](../../DECISIONS.md) - All architectural decisions
- [PROGRESS.md](../../PROGRESS.md) - All session summaries
- [BACKLOG.md](../../BACKLOG.md) - Polish items for future sessions

---

*Game analysis successfully implemented with comprehensive move-by-move evaluation and export capabilities.*
