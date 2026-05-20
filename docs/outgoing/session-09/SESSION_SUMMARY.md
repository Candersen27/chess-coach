# Session 09 Summary - Play vs Coach Polish & Chat Integration

> **Date:** February 20, 2026
> **Phase:** Phase 2 - AI Coaching Layer
> **Outcome:** Success

---

## What Was Built

This session focused on fixing bugs and adding quality-of-life features to the Play vs Coach mode, plus improving the integration between the game board and the chat coach.

### Bug Fixes

**showStatus ReferenceError (chessboard.html)**
- `showStatus()` was defined inside the chessBoard IIFE but called from global-scope `startGameAsWhite()`/`startGameAsBlack()` functions
- The error in `startGameAsBlack()` prevented execution from reaching `requestCoachMove()`, so the coach never made its first move when playing as black
- Fix: Removed the out-of-scope `showStatus` calls — `updateGameStatus()` already displays the game state

**Draw Detection Not Working (chessboard.html)**
- `checkGameOver()` created a new `Chess(fen)` on every call, which has no move history
- Threefold repetition and 50-move rule could never trigger because they require game history
- Fix: Added `getGameStatus()` to the chessBoard IIFE that queries the actual `game` object with full move history
- Now detects: checkmate, stalemate, threefold repetition, insufficient material, 50-move rule

### Board Orientation

**Player perspective (chessboard.html)**
- Board now automatically orients to the player's perspective when starting a game
- Playing as white: white pieces at bottom; playing as black: black pieces at bottom
- Added `orient(color)` function to the chessBoard IIFE public API

**Coach tool support (coach.py + chessboard.html)**
- Added `orientation` parameter to `set_board_position` tool schema
- Coach can now orient the board for puzzles (e.g., `"orientation": "black"` when black is to move)
- Frontend applies orientation in `switchToCoachDemo()`

### Resign & Draw Buttons

**UI (chessboard.html)**
- Draw and Resign buttons appear between the new game buttons and game status during active games
- Hidden when no game is active; disappear on game end
- Draw button styled amber (`#f59e0b`), Resign button styled red (`#c62828`)

**Smart Draw Evaluation (chessboard.html)**
- Draw offers are evaluated by Stockfish at depth 15 before acceptance
- Computer accepts draw only if its position is equal or worse (eval ≤ 0.0 from its perspective)
- Shows "Evaluating draw offer..." while analyzing, "Draw declined!" if rejected
- Button disabled during evaluation to prevent double-clicks

### Captured Pieces Display

**Visual inventory (chessboard.html)**
- Two rows flanking the board show captured pieces for each player
- Uses the existing piece theme images at 22px size
- Material advantage shown as a `+N` badge (standard piece values: P=1, N=3, B=3, R=5, Q=9)
- Orientation-aware: player's captures always at bottom, opponent's at top
- Updates on every move, navigation, reset, position set, flip, and orient
- Computed by parsing FEN and comparing against starting piece counts

### Start Game Tool

**Backend (coach.py + main.py)**
- New `START_GAME_TOOL` allows Claude to start a Play vs Coach game from chat
- Parameters: `player_color` ("white" or "black")
- User can say "let's play a game as black" and the coach triggers the game

**Frontend (chessboard.html)**
- Chat response handler detects `game_action` and calls `startGameAsWhite()`/`startGameAsBlack()`

### Token Usage Display

**Backend (coach.py + main.py)**
- Extracts token usage from Anthropic API response (input, output, cache creation, cache read)
- Added `usage` field to `ChatResponse` model

**Frontend (chessboard.html)**
- Tracks cumulative session token usage
- Displays running total below chat input: `Tokens: 1,234 (in: 1,000, out: 234, cached: 800)`

### PGN Context for Chat

**Backend + Frontend**
- Chat messages now include the current PGN in `board_context`
- Added `pgn` field to `BoardContext` model
- System prompt includes game notation so the coach can discuss games after they end

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `src/backend/coach.py` | Modified | Added `START_GAME_TOOL`, `orientation` param on board tool, token usage extraction, PGN in board context |
| `src/backend/main.py` | Modified | Added `pgn` to `BoardContext`, `game_action` and `usage` to `ChatResponse` |
| `src/frontend/chessboard.html` | Modified | All frontend changes: bug fixes, orientation, draw/resign, captured pieces, token usage, start_game handling, PGN context |

---

## Commits

| Hash | Description |
|------|-------------|
| `8b02c0b` | Fix: Remove out-of-scope showStatus calls in Play vs Coach mode |
| `7f1c04c` | Feat: Add board orientation, draw detection, and resign/draw buttons |
| `0c21a8a` | Feat: Add start_game tool, captured pieces display, token usage, and PGN context |
| `f142319` | Feat: Evaluate draw offers with Stockfish before accepting |

---

## Key Implementation Details

**Draw Detection Fix:**
- Root cause: `new Chess(fen)` creates a game with no history — repetition detection requires the full move sequence
- Solution: Exposed `getGameStatus()` from the IIFE that delegates to the actual `game` object's `in_threefold_repetition()`, `insufficient_material()`, etc.

**Captured Pieces Computation:**
- Parse FEN piece placement field, count each piece type on the board
- Compare against known starting counts (e.g., 8 pawns, 2 knights per side)
- Difference = captured pieces; rendered as small piece images sorted by value (Q, R, B, N, P)

**Draw Offer Evaluation:**
- Calls existing `/api/analyze` endpoint with depth 15
- Evaluation is from white's perspective (standard Stockfish convention)
- Flips sign based on which color the computer plays
- Accepts if `computerAdvantage <= 0`

**Token Usage Tracking:**
- Uses `response.usage.input_tokens`, `output_tokens`, and cache fields from Anthropic API
- `cache_creation_input_tokens` and `cache_read_input_tokens` accessed via `getattr()` for compatibility

---

## Not Yet Implemented (Future Sessions)

- Running commentary during Play vs Coach games (Claude narrating moves as they happen)
- Coach declining draws with explanation of why (currently just "Draw declined!")
- ELO-aware draw acceptance thresholds
- Game result tracking and win/loss statistics
