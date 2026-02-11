# Session 07 Summary - Multi-Game Batch Analysis with Pattern Detection

> **Date:** February 10, 2025
> **Phase:** Phase 2 - AI Coaching Layer
> **Outcome:** Success

---

## What Was Built

### Pattern Detection Module (`src/backend/patterns.py`)
- `PatternDetector` class analyzes batches of analyzed games for recurring tactical weaknesses
- Detects 4 tactical motifs in blunder/mistake positions:
  - **Hanging pieces** — undefended pieces under attack (reports highest-value)
  - **Knight forks** — knights attacking 2+ valuable pieces (checks existing positions and one-move destinations)
  - **Pins** — pieces pinned to the king (identifies the pinning piece)
  - **Back rank** — king trapped by own pawns with opponent heavy piece available
- Phase performance analysis: opening (moves 1-15), middlegame (16-40), endgame (41+)
- Calculates per-phase accuracy, blunder count, mistake count
- Generates top 3 actionable recommendations based on pattern frequency and phase weaknesses
- Overall accuracy calculated from user's color only (when username provided)

### Batch Analysis Endpoint (`src/backend/main.py`)
- `POST /api/games/analyze-batch` — analyzes 5+ PGNs in a single request
- `BatchAnalysisRequest` model: `pgns` (list of PGN strings), `depth` (default 15), `username` (optional)
- Username filtering: parses PGN headers to determine which color the user played, analyzes only their moves
- Returns `analyzed_games` (per-game Stockfish analysis) and `pattern_summary` (aggregated patterns)
- Validates minimum 5 games; reports per-game errors if some fail

### Coach Context Integration (`src/backend/coach.py`)
- `chat()` method accepts optional `pattern_context` parameter
- Pattern data formatted as system prompt block with:
  - Total games analyzed and overall accuracy
  - Tactical weaknesses by type (instance count + games affected)
  - Performance by phase (accuracy, blunders, mistakes)
  - Top 3 recommendations
- Instructs Claude to reference specific patterns and recommend targeted practice

### Frontend: Batch Analysis Tab (`src/frontend/chessboard.html`)
- New "Batch Analysis" tab alongside existing Analysis/Play/Game panels
- Username input field (optional, for filtering to user's moves)
- Large textarea for pasting 5-10 PGNs (split by blank lines)
- Analyze and Clear buttons with loading state
- Pattern summary display:
  - Games analyzed + overall accuracy cards
  - Top recommendations box (highlighted)
  - Tactical patterns with instance details (first 3 shown per pattern)
  - Phase accuracy stats (opening/middlegame/endgame)
- Export analysis as JSON file download
- Import previously exported analysis
- localStorage persistence (auto-saves and auto-loads on page refresh)
- Pattern context passed to chat endpoint when batch analysis data exists

### Sample Data
- Added `data/samples/chrandersen_samples.txt` — 6 real Chess.com games for testing

---

## Architecture After Session 07

```
Frontend (chessboard.html)
├── Chessboard (chessboard.js + chess.js)
├── Analysis/Play/Game/Batch Analysis panels
└── Chat panel ──→ POST /api/chat ──→ coach.py ──→ Claude API
    │                                    ├── BookLibrary (book content in system prompt)
    │                                    ├── LessonManager (lesson plan extraction)
    │                                    └── Pattern context (batch analysis data)
    └── Batch Analysis tab ──→ POST /api/games/analyze-batch ──→ main.py
                                    ├── engine.analyze_game() per PGN
                                    └── PatternDetector.analyze_games()

Backend (FastAPI)
├── main.py (routes: health, analyze, move, game/analyze, games/analyze-batch, chat, books)
├── engine.py (Stockfish wrapper)
├── coach.py (Claude API + book integration + lesson plans + pattern context) ← MODIFIED
├── books.py (Book library module)
├── lesson.py (Lesson plan models and management)
└── patterns.py (Tactical pattern detection + phase analysis) ← NEW

Data
├── data/books/chess_fundamentals_capablanca.txt (raw text)
├── data/books/chess_fundamentals.json (structured, 240KB)
└── data/samples/chrandersen_samples.txt (6 test PGNs) ← NEW
```

---

## New/Modified API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/games/analyze-batch` | POST | Analyze 5+ games, return per-game analysis and aggregated pattern summary |
| `/api/chat` | POST | Now accepts optional `pattern_context` for data-driven coaching |

---

## Data Flow

```
User pastes 5-10 PGNs + optional username
    ↓
POST /api/games/analyze-batch
    ↓
For each PGN:
    engine.analyze_game() → move-by-move Stockfish analysis
    Parse PGN headers → determine user's color (if username provided)
    ↓
PatternDetector.analyze_games():
    _detect_tactical_patterns() → scan blunders/mistakes for motifs
    _analyze_phase_performance() → accuracy/errors by opening/middle/endgame
    _generate_recommendations() → top 3 actionable suggestions
    _calculate_overall_accuracy() → weighted by user's color
    ↓
Response: { analyzed_games, pattern_summary }
    ↓
Frontend: Display patterns, save to localStorage
    ↓
On chat: pattern_context included in /api/chat request
    ↓
Coach: Claude receives pattern data in system prompt → personalized coaching
```

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `src/backend/patterns.py` | Created | Pattern detection module (454 lines) |
| `src/backend/main.py` | Modified | Added batch analysis endpoint + `BatchAnalysisRequest` model |
| `src/backend/coach.py` | Modified | Added `pattern_context` handling in system prompt and `chat()` |
| `src/frontend/chessboard.html` | Modified | Added Batch Analysis tab, state management, export/import |
| `data/samples/chrandersen_samples.txt` | Created | 6 sample Chess.com PGNs for testing |

---

## Key Implementation Details

**Pattern Detection Algorithm:**
1. For each game, iterate over moves classified as blunder or mistake
2. Skip opponent's moves when username filtering is active
3. Reconstruct board position from `fen_after` the bad move
4. Run each tactical detector in priority order (hanging piece → fork → pin → back rank)
5. First match wins — one pattern per blunder
6. Store instance with game index, move number, material lost, FEN, description
7. Aggregate across all games

**Material Values:** Pawn=1, Knight/Bishop=3, Rook=5, Queen=9, King=100

**Accuracy Formula:** `accuracy = max(0, min(100, 100 - (avg_cp_loss / 2)))` (consistent with DECISION-012)

**Recommendation Logic:**
1. Most frequent tactical pattern (requires 2+ instances)
2. Weakest phase vs strongest (if gap >5% or 2+ blunders in weak phase)
3. Second most frequent pattern (1+ instances)
4. Fallback: list blunder-heavy phases

---

## Not Yet Implemented (Future Sessions)

- Claude controlling the board based on lesson plans
- Loading FEN positions from lesson plans onto the chessboard
- Real-time coaching commentary during practice activities
- Multi-PV move selection during coached play
- Advanced pattern categories (discovered attacks, skewers are defined as enums but not yet detected)
- Database persistence for analysis history
