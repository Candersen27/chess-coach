# Session 04 Context - Full Game Analysis + PGN Export

> **Date:** January 23, 2025
> **Phase:** Phase 1 - Technical Foundation
> **Session Goal:** Build full game analysis endpoint and PGN export functionality

---

## What Exists (Session 03 Complete)

### Backend
- `src/backend/main.py` — FastAPI with endpoints:
  - `GET /api/health`
  - `POST /api/analyze` (single position)
  - `POST /api/move` (play vs coach)
- `src/backend/engine.py` — Async Stockfish wrapper with:
  - `analyze(fen, depth)` — single position analysis
  - `get_move(fen, elo)` — ELO-calibrated move

### Frontend
- `src/frontend/chessboard.html`:
  - PGN loading and navigation
  - Single position analysis with "Analyze Position" button
  - Play vs Coach mode with ELO selection
  - Game over detection

### Documentation
- `docs/DECISIONS.md` — 10 decisions logged
- `docs/PROGRESS.md` — Sessions 0-3 logged
- `docs/ARCHITECTURE.md` — System overview

---

## What We're Building This Session

### 1. Full Game Analysis Endpoint

Analyze every move in a PGN, classify quality, calculate accuracy.

**Endpoint:** `POST /api/game/analyze`

**Request:**
```json
{
  "pgn": "[Event \"Game\"]\n\n1. e4 e5 2. Nf3 Nc6...",
  "depth": 15
}
```

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
      "eval_before": 0.3,
      "eval_after": 0.25,
      "eval_change": -0.05,
      "best_move_san": "e4",
      "best_move_uci": "e2e4",
      "classification": "good",
      "is_book": false
    },
    ...
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

### 2. Move Classification

Based on centipawn loss (eval change when it's your turn):

| Classification | CP Loss | Description |
|----------------|---------|-------------|
| Excellent | ≤ 0 | As good or better than engine |
| Good | 0-20 | Solid move |
| Inaccuracy | 20-50 | Slight mistake |
| Mistake | 50-100 | Significant error |
| Blunder | > 100 | Serious error |

**Note:** CP loss calculated from the moving side's perspective. Positive = lost advantage.

### 3. Accuracy Calculation

Formula (Chess.com style):
```
accuracy = 103.1668 * exp(-0.04354 * avg_centipawn_loss) - 3.1668
```

Or simpler approximation:
```
accuracy = max(0, 100 - (avg_centipawn_loss / 2))
```

### 4. Analysis Display (Frontend)

- Move list with color coding:
  - Green: Excellent/Good
  - Yellow: Inaccuracy
  - Orange: Mistake
  - Red: Blunder
- Click move to jump to that position
- Show accuracy percentages for White/Black
- Highlight critical moments

### 5. PGN Export

Two export options:
- **Plain PGN:** Just moves (what you played)
- **Annotated PGN:** Moves + evaluations + best alternatives in comments

**Annotated format:**
```
1. e4 {+0.3} e5 {+0.25} 2. Bc4?? {Blunder. +0.25 → -1.2. Best: Nf3} ...
```

---

## Technical Decisions (Pre-Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Classification thresholds | 0/20/50/100 CP | Standard Chess.com-like thresholds |
| Accuracy formula | Simple approximation | Good enough for MVP, can refine later |
| Analysis depth | 15 (default) | Consistent with single-position analysis |
| Export format | Standard PGN with {} comments | Compatible with all chess software |

---

## Data Flow for Future Agent

This analysis output is designed for the coaching agent (Session 06):

```
Agent receives:
├── Move-by-move evaluations
├── Classifications (where you went wrong)
├── Best alternatives (what you should have played)
├── Accuracy metrics (how well you played overall)
└── Critical moments (key turning points)

Agent can then:
├── Identify patterns ("You blundered 3 times in endgames")
├── Compare to profile ("Your opening was better this game")
├── Reference books ("This pawn structure is covered in...")
└── Give targeted advice ("Practice rook endgames")
```

---

## Backlog Item

Create `docs/BACKLOG.md` for tracking polish items:
- Click-click piece movement (alternative to drag)
- Drag fluidity improvements

---

## Commands Reference

```bash
# Navigate to project
cd ~/myCodes/projects/chess-coach

# Activate venv
source venv/bin/activate

# Run backend
cd src/backend
uvicorn main:app --reload --port 8000

# Test game analysis endpoint
curl -X POST http://localhost:8000/api/game/analyze \
  -H "Content-Type: application/json" \
  -d '{"pgn": "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6", "depth": 15}'
```

---

## Reference Files

- `docs/outgoing/session-03/SESSION_SUMMARY.md` — Previous session
- `docs/outgoing/session-01/STOCKFISH_INTEGRATION_GUIDE.md` — Engine details
- `data/samples/*.pgn` — Test PGN files
