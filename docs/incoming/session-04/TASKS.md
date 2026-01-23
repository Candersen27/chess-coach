# Session 04 Tasks - Full Game Analysis + PGN Export

---

## Pre-Session Task: Create Backlog

- [ ] Create `docs/BACKLOG.md` with the following content:

```markdown
# Development Backlog

Items to address in future polish sessions.

---

## UI Polish

### Click-Click Piece Movement
**Priority:** Medium
**Added:** Session 03
**Description:** Alternative to drag-drop. Click piece to select, click destination to move. Improves accessibility and feels more natural on some devices.

### Drag Fluidity
**Priority:** Low
**Added:** Session 03
**Description:** Investigate chessboard.js drag threshold settings. Current drag can feel slightly sluggish.

---

## Future Features

(Add items here as they come up)

---

*Review this list periodically during polish sessions.*
```

---

## Task 1: Backend - Game Analysis Endpoint

### 1.1: Update engine.py

- [ ] Add `analyze_game(pgn, depth)` method to ChessEngine class
- [ ] Parse PGN and iterate through all moves
- [ ] For each position:
  - Get evaluation before move
  - Get best move
  - Apply the actual move
  - Get evaluation after
  - Calculate eval change (centipawn loss)
  - Classify move quality
- [ ] Handle edge cases:
  - Checkmate positions (eval = mate)
  - Very short games
  - Invalid PGN
- [ ] Return structured analysis data

**Method signature:**
```python
async def analyze_game(self, pgn: str, depth: int = 15) -> Dict[str, Any]:
    """Analyze all moves in a PGN game."""
    pass
```

### 1.2: Add Classification Logic

- [ ] Create `classify_move(cp_loss)` function:

```python
def classify_move(cp_loss: float) -> str:
    """Classify move based on centipawn loss."""
    if cp_loss <= 0:
        return "excellent"
    elif cp_loss <= 20:
        return "good"
    elif cp_loss <= 50:
        return "inaccuracy"
    elif cp_loss <= 100:
        return "mistake"
    else:
        return "blunder"
```

### 1.3: Add Accuracy Calculation

- [ ] Create `calculate_accuracy(cp_losses)` function:

```python
def calculate_accuracy(cp_losses: List[float]) -> float:
    """Calculate accuracy percentage from list of centipawn losses."""
    if not cp_losses:
        return 100.0
    avg_loss = sum(abs(loss) for loss in cp_losses) / len(cp_losses)
    accuracy = max(0, min(100, 100 - (avg_loss / 2)))
    return round(accuracy, 1)
```

### 1.4: Update main.py

- [ ] Add request/response models:

```python
class GameAnalysisRequest(BaseModel):
    pgn: str
    depth: int = 15

class MoveAnalysis(BaseModel):
    move_number: int
    color: str  # "white" or "black"
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

- [ ] Implement `POST /api/game/analyze` endpoint
- [ ] Handle errors (invalid PGN, engine errors)
- [ ] Return 400 for invalid PGN, 500 for engine errors

---

## Task 2: Frontend - Analysis Display

### 2.1: Add Analysis UI Panel

- [ ] Create "Game Analysis" section in HTML
- [ ] Add "Analyze Game" button (analyzes loaded PGN)
- [ ] Add analysis results panel:
  - Accuracy display (White: 85% | Black: 78%)
  - Move counts (Blunders: 1 | Mistakes: 2 | Inaccuracies: 3)
  - Move list with color coding

### 2.2: Implement Analysis JavaScript

- [ ] Create `analyzeFullGame()` function:
  - Get current PGN from loaded game
  - POST to /api/game/analyze
  - Display loading state ("Analyzing... this may take a minute")
  - Handle response and display results

- [ ] Create `displayGameAnalysis(data)` function:
  - Populate accuracy display
  - Build color-coded move list
  - Highlight critical moments

- [ ] Create `getMoveColor(classification)` function:
```javascript
function getMoveColor(classification) {
    switch(classification) {
        case 'excellent': return '#2ecc71';  // Green
        case 'good': return '#27ae60';       // Dark green
        case 'inaccuracy': return '#f1c40f'; // Yellow
        case 'mistake': return '#e67e22';    // Orange
        case 'blunder': return '#e74c3c';    // Red
        default: return '#95a5a6';           // Gray
    }
}
```

### 2.3: Move List Interaction

- [ ] Make moves in analysis list clickable
- [ ] Clicking move jumps board to that position
- [ ] Show tooltip with eval change and best move on hover

---

## Task 3: PGN Export

### 3.1: Backend - Export Endpoint (Optional)

Could handle entirely in frontend, but backend option allows annotated export:

- [ ] Add `POST /api/game/export` endpoint (optional)
- [ ] Or handle export purely in frontend JavaScript

### 3.2: Frontend - Export Functions

- [ ] Create `exportPGN(annotated)` function:
  - If annotated=false: plain moves only
  - If annotated=true: include {eval} and comments for bad moves

- [ ] Create `generateAnnotatedPGN(analysisData)` function:
```javascript
function generateAnnotatedPGN(moves) {
    let pgn = "";
    for (const move of moves) {
        if (move.color === 'white') {
            pgn += `${move.move_number}. `;
        }
        pgn += move.move_san;
        
        // Add annotation for non-good moves
        if (['blunder', 'mistake', 'inaccuracy'].includes(move.classification)) {
            pgn += ` {${move.classification}. ${move.eval_before} → ${move.eval_after}. Best: ${move.best_move_san}}`;
        } else {
            pgn += ` {${move.eval_after > 0 ? '+' : ''}${move.eval_after}}`;
        }
        pgn += ' ';
    }
    return pgn.trim();
}
```

- [ ] Create `downloadPGN(content, filename)` function:
```javascript
function downloadPGN(content, filename) {
    const blob = new Blob([content], { type: 'application/x-chess-pgn' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}
```

### 3.3: Export UI

- [ ] Add "Export PGN" dropdown or buttons:
  - "Export Plain PGN"
  - "Export Annotated PGN" (after analysis)
- [ ] Generate filename: `game_YYYY-MM-DD_HHmm.pgn`
- [ ] Works for:
  - Loaded PGN files
  - Games played vs coach

---

## Task 4: Testing

### Backend Tests

- [ ] Test with sample PGN from `data/samples/`
- [ ] Verify move-by-move analysis returns
- [ ] Verify classification logic:
  - Force a blunder position, check classification
  - Check excellent move (matches engine best)
- [ ] Verify accuracy calculation
- [ ] Test invalid PGN handling
- [ ] Test very short game (2-3 moves)
- [ ] Test game with checkmate

### Frontend Tests

- [ ] Load PGN → Click "Analyze Game" → See results
- [ ] Verify color coding matches classifications
- [ ] Click move in list → Board jumps to position
- [ ] Export plain PGN → Opens valid file
- [ ] Export annotated PGN → Includes evaluations
- [ ] Export game played vs coach

### Performance Test

- [ ] Analyze 40-move game
- [ ] Should complete in reasonable time (~1-2 min at depth 15)
- [ ] Consider adding progress indicator

---

## Task 5: Documentation

- [ ] Update `docs/DECISIONS.md`:
  - DECISION-011: Move classification thresholds
  - DECISION-012: Accuracy formula choice

- [ ] Update `docs/PROGRESS.md` with Session 04 summary

- [ ] Create `docs/outgoing/session-04/SESSION_SUMMARY.md`

- [ ] Create `docs/outgoing/session-04/README.md`

---

## Deliverables Checklist

- [ ] `docs/BACKLOG.md` created
- [ ] `POST /api/game/analyze` endpoint working
- [ ] Move classification logic implemented
- [ ] Accuracy calculation implemented
- [ ] Frontend analysis display with color-coded moves
- [ ] Clickable move list (jump to position)
- [ ] PGN export (plain)
- [ ] PGN export (annotated, after analysis)
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Git committed and pushed

---

## File Structure After Session

```
chess-coach/
├── src/
│   ├── backend/
│   │   ├── main.py              # Updated with /api/game/analyze
│   │   ├── engine.py            # Updated with analyze_game()
│   │   └── requirements.txt
│   └── frontend/
│       └── chessboard.html      # Updated with analysis UI + export
├── docs/
│   ├── BACKLOG.md               # NEW - polish items
│   ├── DECISIONS.md             # Updated
│   ├── PROGRESS.md              # Updated
│   ├── ARCHITECTURE.md
│   ├── incoming/session-04/
│   └── outgoing/session-04/
│       ├── SESSION_SUMMARY.md
│       └── README.md
└── ...
```

---

## Performance Considerations

- Full game analysis is slow (~2-4 seconds per move at depth 15)
- 40-move game = ~80 positions = 2-5 minutes total
- Consider:
  - Progress indicator ("Analyzing move 12/48...")
  - Lower default depth for game analysis (depth 12?)
  - Option to analyze specific move range

---

## Notes for Claude Code

- Analysis output structure is designed for future agent consumption
- PGN export creates bridge for data persistence (before database exists)
- Keep UI functional, not fancy—polish comes later
- Test with the sample PGN in `data/samples/`
- The 500ms delays and loading states improve UX significantly
