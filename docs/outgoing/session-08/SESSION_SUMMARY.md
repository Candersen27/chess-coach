# Session 08 Phase 1 Summary - Board Control Foundation

> **Date:** February 11, 2025
> **Phase:** Phase 2 - AI Coaching Layer
> **Outcome:** Success

---

## What Was Built

### Stockfish Coaching Methods (`src/backend/engine.py`)
- `get_coaching_context(fen, depth)` — comprehensive position analysis for coaching:
  - Position evaluation (in pawns, from White's perspective)
  - Top 3 candidate moves with SAN notation and individual evaluations
  - Mate detection (mate_in field)
  - Uses `multipv=3` on the existing python-chess async engine interface
- `evaluate_move(fen, move_san, depth)` — before/after move analysis:
  - Evaluates position before and after a given move
  - Computes eval loss from the moving player's perspective
  - Classifies move quality using existing `classify_move()` thresholds (DECISION-011)
  - Returns best move and top alternatives for coaching context

### Tool Calling Infrastructure (`src/backend/coach.py`)
- `BOARD_CONTROL_TOOL` — Anthropic tool definition for `set_board_position`:
  - Parameters: `fen` (required), `annotation` (required), `moves` (optional, empty in Phase 1)
  - Description guides Claude on when to show positions (tactics, concepts, consequences)
- System prompt updated with board control capability instructions
- `chat_with_tools(message, conversation_history, board_context, pattern_context)`:
  - Calls Claude API with `tools=[BOARD_CONTROL_TOOL]`
  - Iterates `response.content` blocks to extract text and tool_use data
  - Returns `{message, board_control, suggested_action}` — board_control is `{fen, annotation, moves}` or `null`
  - Coexists with existing lesson plan extraction (`[LESSON_PLAN]` marker)
- `chat()` method refactored as backward-compatible wrapper around `chat_with_tools()`

### Coach Move Endpoint (`src/backend/main.py`)
- `POST /api/coach/move` — handles user moves in Coach Demo mode:
  - Request: `{fen, move, context}` where `fen` is the position BEFORE the move
  - Pipeline: Stockfish `evaluate_move()` → build coaching prompt with engine data → Claude `chat_with_tools()`
  - Response: `{message, board_control, stockfish_eval, status}`
  - Claude receives eval before/after, loss, classification, best move — coaches based on that data
  - If move is a mistake/blunder, Claude may use `set_board_position` to show consequences
- `POST /api/chat` updated:
  - Now calls `chat_with_tools()` instead of `chat()`
  - Returns `board_control` field in `ChatResponse` model
  - Backward compatible — `board_control` is `null` when Claude doesn't show a position
- `CoachMoveRequest` Pydantic model added
- `ChatResponse` model extended with `board_control: Optional[dict]`

### Frontend: Mode Toggle & Interactive Board (`src/frontend/chessboard.html`)

**Mode Toggle UI:**
- "My Game" / "Coach Demo" buttons above the chessboard
- Active mode highlighted with green styling
- "Coach Demo" button disabled until Claude shows a position

**Game State Management:**
- `gameState` object tracks both modes independently:
  - `myGame`: PGN, currentMove index, FEN
  - `coachDemo`: positions array, FEN, interactive flag
  - `activeMode`: which mode is active
  - `isWaitingForCoach`: prevents moves during API calls
- `switchToCoachDemo(boardControl)` — auto-called when Claude uses the tool:
  - Saves current My Game state (PGN + move position)
  - Loads new position, updates toggle buttons, shows annotation
- `switchToMyGame()` — restores user's game exactly where they left off
- `switchToCoachDemoManual()` — for clicking the button (restores last coach position)

**Interactive Moves:**
- `onDragStart` modified — allows piece dragging in Coach Demo mode (blocks when waiting for coach)
- `onDrop` modified — captures FEN before move, validates, then calls `handleCoachDemoMove()`
- `handleCoachDemoMove(fenBefore, moveSan)`:
  - Shows "Coach is analyzing..." indicator in chat
  - Sends `{fen, move, context}` to `/api/coach/move`
  - Displays Claude's coaching response in chat
  - Updates board if Claude demonstrates a new position

**Supporting Features:**
- `buildPGNFromFEN(fen)` — generates PGN with `[FEN]` and `[SetUp]` headers
- Annotation panel below board (amber background) shows Claude's position explanations
- `getCurrentMode()` updated to report `'coachDemo'` when in that mode
- `sendChatMessage()` handles `board_control` in `/api/chat` responses

---

## Architecture After Session 08

```
Frontend (chessboard.html)
├── Mode Toggle: [My Game] [Coach Demo]
├── Chessboard (chessboard.js + chess.js)
│   ├── My Game: view-only, uploaded PGN navigation
│   └── Coach Demo: interactive, moves sent to /api/coach/move
├── Annotation Panel (position explanations from Claude)
├── Analysis/Play/Game/Batch Analysis panels
└── Chat panel
    ├── POST /api/chat ──→ coach.chat_with_tools() ──→ Claude API (with tools)
    │                         ├── Text response → chat message
    │                         └── set_board_position tool → board_control → board update
    └── POST /api/coach/move ──→ engine.evaluate_move() → coach.chat_with_tools()
                                   └── Stockfish analysis + Claude coaching

Backend (FastAPI)
├── main.py (routes: health, analyze, move, game/analyze, games/analyze-batch, chat, coach/move, books)
├── engine.py (Stockfish wrapper + get_coaching_context + evaluate_move) ← MODIFIED
├── coach.py (Claude API + tools + book integration + lessons + patterns) ← MODIFIED
├── books.py (Book library module)
├── lesson.py (Lesson plan models and management)
└── patterns.py (Tactical pattern detection + phase analysis)
```

---

## New/Modified API Endpoints

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/coach/move` | POST | **New** | Evaluate user move with Stockfish, get Claude coaching feedback |
| `/api/chat` | POST | Modified | Now returns `board_control` when Claude demonstrates positions |

---

## Data Flow

### Scenario 1: Claude Demonstrates a Position

```
User: "Show me a knight fork"
    ↓
POST /api/chat
    ↓
coach.chat_with_tools() → Claude API (with set_board_position tool)
    ↓
Claude response: text block + tool_use block
    ↓
Parse: message = text, board_control = {fen, annotation, moves: []}
    ↓
Response: {message, board_control, suggested_action}
    ↓
Frontend: addChatMessage() + switchToCoachDemo(board_control)
    ↓
Board updates, mode switches to Coach Demo, annotation shown
```

### Scenario 2: User Makes Move in Coach Demo

```
User drags piece (e.g., Nf6)
    ↓
onDrop: capture fenBefore, validate move, update board
    ↓
handleCoachDemoMove(fenBefore, "Nf6")
    ↓
POST /api/coach/move {fen: fenBefore, move: "Nf6", context}
    ↓
Backend: engine.evaluate_move(fen, "Nf6", depth=15)
    → get_coaching_context(before) + get_coaching_context(after)
    → eval_loss, classification, best_move
    ↓
Backend: coach.chat_with_tools(coaching_prompt_with_stockfish_data)
    ↓
Response: {message, board_control (optional), stockfish_eval}
    ↓
Frontend: display coaching message, update board if new position shown
```

### Scenario 3: Mode Switching

```
User in My Game (move 15 of uploaded PGN)
    ↓
Claude shows a position → switchToCoachDemo()
    ↓
gameState.myGame = {pgn, currentMove: 14, fen} (saved)
gameState.activeMode = "coachDemo"
Board loads Claude's position
    ↓
User clicks "My Game" button → switchToMyGame()
    ↓
gameState.activeMode = "myGame"
chessBoard.loadPGN(saved PGN) → navigate to move 15
Board restored exactly where user left off
```

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `src/backend/engine.py` | Modified | Added `get_coaching_context()` and `evaluate_move()` methods |
| `src/backend/coach.py` | Modified | Added `BOARD_CONTROL_TOOL`, `chat_with_tools()`, system prompt update, `chat()` refactored as wrapper |
| `src/backend/main.py` | Modified | Added `/api/coach/move` endpoint, `CoachMoveRequest` model, `ChatResponse.board_control`, updated `/api/chat` |
| `src/frontend/chessboard.html` | Modified | Added mode toggle, gameState, interactive moves, annotation panel, coach thinking indicator |
| `docs/DECISIONS.md` | Modified | Added DECISION-021 through DECISION-023 |
| `docs/PROGRESS.md` | Modified | Added Session 08 Phase 1 entry |

---

## Key Implementation Details

**Tool Calling Flow:**
1. Claude API called with `tools=[BOARD_CONTROL_TOOL]` and system prompt describing when to use it
2. Response contains mix of `text` and `tool_use` content blocks
3. Backend iterates blocks, concatenates text, extracts first `set_board_position` tool call
4. `board_control` returned as structured data alongside the text message
5. No tool_result sent back — this is a "fire and forget" tool use (Claude's turn ends)

**Eval Loss Calculation (matching existing `analyze_game` pattern):**
- Both before/after evaluations are from White's perspective (DECISION-006)
- White moved: `loss = eval_before - eval_after`
- Black moved: `loss = eval_after - eval_before`
- Convert to centipawns (`× 100`) for `classify_move()` thresholds

**State Preservation on Mode Switch:**
- My Game state saved: PGN string + current move index + current FEN
- Move index extracted from the display text (chessBoard IIFE doesn't expose it directly)
- Restoration: reload PGN, then step forward to saved move index

**Rate Limiting Consideration:**
- Book content is ~57K tokens, org limit is ~30K tokens/min
- First API call in a session may hit rate limit; prompt caching helps subsequent calls
- `/api/coach/move` calls are separate from `/api/chat` and both count against the limit

---

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| DECISION-021 | Anthropic native tool calling for board control | Most robust, extensible, no brittle parsing |
| DECISION-022 | Two-mode board (My Game / Coach Demo) | Clear mental model, state preservation, no accidental game modification |
| DECISION-023 | Stockfish + Claude hybrid coaching for moves | Engine accuracy + natural language explanation |

---

## Not Yet Implemented (Phase 2 / Future Sessions)

- Arrow and highlight annotations on the board
- Move sequences in single tool call (Phase 1 = single positions only)
- Structured lesson navigation UI (step through activities)
- Claude adaptive Stockfish queries (deeper analysis on request)
- Variation trees (backtracking currently clears forward moves)
- Progress tracking / lesson completion
- Database persistence for game state and coaching sessions
