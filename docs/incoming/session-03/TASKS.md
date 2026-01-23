# Session 03 Tasks - Documentation Cleanup + Play vs Coach

---

## ⚠️ THIS SESSION HAS TWO PARTS

**Part A:** Documentation cleanup → **STOP FOR GIT COMMIT**
**Part B:** Play vs Coach feature build

Complete Part A fully, commit, then proceed to Part B.

---

# PART A: Documentation Cleanup

## Task A1: Consolidate Project-Wide Documents

### A1.1: Update docs/DECISIONS.md
- [ ] Open existing `docs/DECISIONS.md`
- [ ] Add Session 02 decisions (see CONTEXT.md for full text):
  - DECISION-005: FastAPI for Backend Framework
  - DECISION-006: Evaluation from White's Perspective
  - DECISION-007: Keep Engine Alive Between Requests
  - DECISION-008: Default Analysis Depth of 15
- [ ] Ensure all decisions follow the standard format

### A1.2: Update docs/PROGRESS.md
- [ ] Open existing `docs/PROGRESS.md`
- [ ] Add Session 02 summary:
  ```markdown
  ## Session 02 - 2025-01-23 (Backend + Stockfish)

  **Goal:** Build FastAPI backend with Stockfish analysis
  **Duration:** ~1 hour
  **Outcome:** Success

  ### Accomplished
  - Created FastAPI backend with async Stockfish wrapper
  - Implemented /api/health and /api/analyze endpoints
  - Added "Analyze Position" button to frontend
  - Color-coded evaluation display (green/red)
  - Mate-in-X detection

  ### Issues Encountered
  - python-chess async API returns tuple (transport, protocol)
  - Switched from .relative to .white() for standard eval convention

  ### Next Session
  - Play against Stockfish with ELO calibration
  ```

### A1.3: Create docs/ARCHITECTURE.md
- [ ] Create new file `docs/ARCHITECTURE.md`
- [ ] Pull relevant content from `docs/outgoing/session-01/ARCHITECTURE_OVERVIEW.md`
- [ ] Update to reflect current state (backend now exists)
- [ ] Keep it concise—this is the living reference, not a deep dive

### A1.4: Clean Up Old Files
- [ ] Remove `docs/CLAUDE_CODE_CONTEXT.md` (superseded by incoming/session-XX docs)
- [ ] Verify `docs/incoming/session-01/` only contains session-specific context (not project-wide docs)
- [ ] Do NOT delete outgoing session docs—they're historical records

---

## Task A2: Verify Structure

After cleanup, structure should be:

```
docs/
├── DECISIONS.md              # ✓ Updated with all decisions
├── PROGRESS.md               # ✓ Updated with session summaries  
├── ARCHITECTURE.md           # ✓ Created/consolidated
├── incoming/
│   ├── session-01/
│   ├── session-02/
│   └── session-03/
└── outgoing/
    ├── session-01/
    └── session-02/
```

- [ ] Confirm structure matches above
- [ ] Confirm DECISIONS.md has 8+ decisions logged
- [ ] Confirm PROGRESS.md has Sessions 0, 1, 2 logged

---

## 🛑 STOP HERE - GIT COMMIT

```bash
cd ~/myCodes/projects/chess-coach
git add .
git commit -m "Reorganize documentation structure"
git push
```

**Confirm with user before proceeding to Part B.**

---

# PART B: Play vs Coach Mode

## Task B1: Backend - New Endpoint

### B1.1: Update engine.py
- [ ] Add `get_move(fen, elo)` method to ChessEngine class
- [ ] Configure UCI_LimitStrength and UCI_Elo options
- [ ] Return engine's move in both UCI and SAN format
- [ ] Handle edge cases (game over, invalid position)

```python
async def get_move(self, fen: str, elo: int = 1200) -> dict:
    """Get engine's move at specified ELO level."""
    # Configure strength
    await self.engine.configure({
        "UCI_LimitStrength": True,
        "UCI_Elo": max(800, min(2800, elo))  # Clamp to valid range
    })
    
    board = chess.Board(fen)
    result = await self.engine.play(board, chess.engine.Limit(time=1.0))
    
    return {
        "move": result.move.uci(),
        "move_san": board.san(result.move)
    }
```

### B1.2: Update main.py
- [ ] Add request/response models for move endpoint
- [ ] Implement `POST /api/move` endpoint
- [ ] Accept: `{"fen": "...", "elo": 1200}`
- [ ] Return: `{"move": "e7e5", "move_san": "e5", "fen_after": "..."}`
- [ ] Validate ELO range (800-2800)
- [ ] Handle game-over positions gracefully

---

## Task B2: Frontend - Play Mode UI

### B2.1: Add Play Mode Controls
- [ ] Add "Play vs Coach" section to UI
- [ ] ELO selector (dropdown or slider): 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500, 2800
- [ ] "New Game as White" button
- [ ] "New Game as Black" button
- [ ] Display current game status (your turn / coach thinking / game over)

### B2.2: Implement Game Flow
- [ ] Create `startGameAsWhite()` function:
  - Reset board to starting position
  - Set player color to white
  - Enable piece dragging
  - Wait for player move

- [ ] Create `startGameAsBlack()` function:
  - Reset board to starting position
  - Set player color to black
  - Immediately request coach's first move
  - Then enable piece dragging

- [ ] Create `onPlayerMove(source, target)` handler:
  - Validate move is legal
  - Apply move to board
  - Check for game over
  - If not over, request coach move

- [ ] Create `requestCoachMove()` function:
  - Show "Coach thinking..." status
  - POST to /api/move with current FEN and selected ELO
  - Apply coach's move to board
  - Check for game over
  - Re-enable player moves

### B2.3: Game Over Detection
- [ ] Check for checkmate, stalemate, insufficient material
- [ ] Display result: "Checkmate - You win!", "Checkmate - Coach wins!", "Draw"
- [ ] Disable further moves when game over
- [ ] Show "Play Again" option

---

## Task B3: Testing

### Backend Tests
- [ ] Test `/api/move` with starting position
- [ ] Test with different ELO values (800, 1500, 2500)
- [ ] Test with near-endgame position
- [ ] Test with checkmate position (should return error/no move)
- [ ] Verify move is legal

### Frontend Tests
- [ ] Start game as White, make move, verify coach responds
- [ ] Start game as Black, verify coach moves first
- [ ] Change ELO mid-game, verify affects coach play
- [ ] Play to checkmate, verify game ends correctly
- [ ] Test "New Game" resets properly

### End-to-End
- [ ] Play a complete short game (Scholar's Mate attempt)
- [ ] Verify move notation displays correctly
- [ ] Verify board state stays synchronized

---

## Task B4: Documentation

- [ ] Add DECISION-009: ELO Range 800-2800 (Stockfish's supported range)
- [ ] Add DECISION-010: Frontend manages game state (backend stateless)
- [ ] Update PROGRESS.md with Session 03 summary
- [ ] Create `docs/outgoing/session-03/SESSION_SUMMARY.md`
- [ ] Create `docs/outgoing/session-03/README.md`

---

## Deliverables Checklist

### Part A (Docs Cleanup)
- [ ] docs/DECISIONS.md updated
- [ ] docs/PROGRESS.md updated
- [ ] docs/ARCHITECTURE.md created
- [ ] Old files cleaned up
- [ ] Git committed and pushed

### Part B (Play vs Coach)
- [ ] `/api/move` endpoint working
- [ ] ELO limiting working
- [ ] "New Game as White/Black" buttons
- [ ] Full game playable against coach
- [ ] Game over detection
- [ ] Session 03 outgoing docs created
- [ ] Git committed and pushed

---

## File Structure After Session

```
chess-coach/
├── src/
│   ├── backend/
│   │   ├── main.py              # Updated with /api/move
│   │   ├── engine.py            # Updated with get_move()
│   │   └── requirements.txt
│   └── frontend/
│       ├── chessboard.html      # Updated with play mode
│       └── ...
├── docs/
│   ├── DECISIONS.md             # Updated (project-wide)
│   ├── PROGRESS.md              # Updated (project-wide)
│   ├── ARCHITECTURE.md          # Created (project-wide)
│   ├── incoming/session-03/
│   └── outgoing/session-03/
│       ├── SESSION_SUMMARY.md
│       └── README.md
└── ...
```

---

## Notes for Claude Code

- **Part A first, commit, then Part B.** Don't mix them.
- Reference `docs/outgoing/session-01/STOCKFISH_INTEGRATION_GUIDE.md` for Stockfish details
- Keep UI simple—functionality over polish
- ELO limiting uses Stockfish's built-in options, no custom weakening logic needed
- Game state lives in frontend only; backend just responds to position + ELO
