# Chess Coach: A Deep Dive

> A comprehensive walkthrough of how this AI chess coaching platform works, why we made the decisions we did, and what we learned building it.

---

## 1. What Is This?

Chess Coach is a web application that lets you analyze chess games with Stockfish and play against an AI opponent at adjustable difficulty levels. But it's really a foundation for something more ambitious: an AI chess coach that *remembers* you.

The long-term vision is a system where you can have a conversation with Claude about your chess games, and it actually knows your playing style, your weaknesses, and your progress over time. Phase 1 (what's built now) creates all the chess analysis capabilities that the AI coach will eventually tap into.

What makes this interesting isn't just "another chess analysis tool" - it's the architecture. The entire board can be controlled programmatically, which means an AI can manipulate it while explaining concepts. That's the key insight: the board is a prop for the coach to use, not just a UI for the user.

---

## 2. The Big Picture

Think of the system like a restaurant kitchen:

```
┌─────────────────────────────────────────────────────────────────┐
│                      THE DINING ROOM                            │
│                   (Your Web Browser)                            │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  The Table (chessboard.js)      The Rules (chess.js)    │  │
│   │  - Shows pieces                  - Knows legal moves    │  │
│   │  - Handles drag/drop             - Tracks game state    │  │
│   │  - Pretty to look at             - Parses PGN files     │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  The Chat Panel                                          │  │
│   │  - Talk to your coach           - See conversation       │  │
│   │  - Ask questions                - Get explanations       │  │
│   └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────│──────────────────────────────────┘
                               │
                    Waiter takes orders
                      (HTTP/JSON API)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      THE KITCHEN                                │
│                  (Python FastAPI Server)                        │
│                                                                 │
│   The head chef coordinates everything and                     │
│   talks to the specialists...                                  │
└───────────────────┬─────────────────────┬───────────────────────┘
                    │                     │
         UCI Protocol               Claude API
                    │                     │
                    ▼                     ▼
┌───────────────────────────┐ ┌───────────────────────────────────┐
│      THE ANALYST          │ │         THE COACH                 │
│      (Stockfish)          │ │         (Claude)                  │
│                           │ │                                   │
│  Chess grandmaster who    │ │  Patient teacher who explains    │
│  calculates positions     │ │  concepts and guides learning    │
└───────────────────────────┘ └───────────────────────────────────┘
```

The frontend is what you see and interact with. It handles the visual presentation and basic game logic. When it needs serious analysis - "what's the best move here?" or "how good was that game?" - it asks the backend.

The backend doesn't do much thinking itself. It's mainly a translator between "what the web app needs" and "what Stockfish understands." Stockfish is the actual brain, running as a separate process that stays alive between requests.

---

## 3. The Frontend Story

### Two Libraries, Two Jobs

The frontend uses two JavaScript libraries that might seem redundant but actually have cleanly separated responsibilities:

**chessboard.js** handles everything visual:
- Rendering the 8x8 grid with alternating colors
- Showing piece images in the right squares
- Making pieces draggable
- Animating moves
- Flipping the board view

**chess.js** handles everything logical:
- Knowing what moves are legal from any position
- Parsing PGN notation into moves
- Tracking game state (whose turn, castling rights, etc.)
- Detecting checkmate, stalemate, and draws
- Converting between different move formats (e2e4 vs e4)

This separation is elegant. If you drag a piece, chessboard.js says "piece is moving from e2 to e4." Then we ask chess.js "is that legal?" If yes, we update both. If no, the piece snaps back.

### The Programmatic API: Why It Matters

Here's the key insight that shaped the whole frontend design: the board needed to be controllable by code, not just by human clicks.

```javascript
// The AI coach will eventually do things like:
chessBoard.setPosition("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3");
// "Okay, let me show you this position where you went wrong..."

chessBoard.makeMove("d2", "d4");
// "Now watch what happens if White plays d4 instead..."
```

This is what makes Chess Coach different from a simple analysis board. The board is a teaching tool that an AI can manipulate while explaining concepts.

### Three Modes of Operation

The frontend operates in three modes:

**Navigation Mode:** When you've loaded a PGN file and you're stepping through moves. You can't drag pieces here because you're viewing history. Arrow keys work. The board is a read-only timeline viewer.

**Free Play Mode:** The starting state. You can drag pieces, make moves, explore positions. This is like having a physical board on your desk.

**Play vs Coach Mode:** An actual game against Stockfish. Turn management is enforced - you can only move on your turn. The coach "thinks" (500ms delay for natural feel) and responds. The game ends properly with checkmate/draw detection.

### State Management Without a Framework

The frontend manages state with plain JavaScript variables and a carefully structured module:

```javascript
const chessBoard = (function() {
    let board = null;           // The visual board object
    let game = new Chess();     // The logical game state
    let moveHistory = [];       // Array of {move, fen} objects
    let currentMoveIndex = -1;  // Where we are in the history

    // ... all the functions that manipulate these

    return {
        // Only expose what's needed publicly
        setPosition: setPosition,
        makeMove: makeMove,
        loadPGN: loadPGN,
        // etc.
    };
})();
```

This IIFE (Immediately Invoked Function Expression) pattern keeps the internal state private while exposing a clean public API. It's simple, it works, and it doesn't require React or Vue or any framework. For a focused single-page application like this, that simplicity is a feature.

---

## 4. The Backend Story

### Why FastAPI Instead of Flask

Flask would have worked fine. But FastAPI was chosen for three reasons:

1. **Native async support.** Stockfish runs as a subprocess, and communicating with it is I/O-bound. Async lets us handle this elegantly without blocking.

2. **Auto-generated API docs.** Hit `/docs` and you get a fully interactive Swagger UI. Hit `/redoc` for a cleaner reference. For free. No extra code.

3. **Pydantic models.** Request/response validation happens automatically. Define a model, and FastAPI validates incoming JSON against it. Typos and type mismatches get caught at the API boundary, not deep in your code.

The learning curve is slightly steeper than Flask, but for a project that will eventually have a real API surface (Claude integration, possibly mobile clients), it's the right foundation.

### Talking to Stockfish: The UCI Protocol

Stockfish is a chess engine that runs as its own process. It doesn't import into Python - you launch it, then communicate via text commands over stdin/stdout. This is the UCI (Universal Chess Interface) protocol.

Think of it like passing notes under a door:

```
You: "uci"
Stockfish: "id name Stockfish 16..." (tells you about itself)
Stockfish: "uciok" (ready to work)

You: "position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
(set up this specific position)

You: "go depth 15"
(analyze to depth 15)

Stockfish: "info depth 1 score cp 32 pv e7e5..."
Stockfish: "info depth 2 score cp 28 pv e7e6..."
... (thinking out loud)
Stockfish: "bestmove e7e5 ponder d2d4"
(here's my answer)
```

The python-chess library handles all this protocol stuff for us. We call `engine.analyse(board, limit)` and get back a nice Python dictionary. But understanding what's happening underneath helps when things go wrong.

### Keeping the Engine Alive

A key architectural decision: we start Stockfish once when the server boots, and keep it running until the server shuts down.

The alternative would be spawning a new Stockfish process for each request. But Stockfish has startup overhead - loading opening books, initializing hash tables, etc. By keeping it alive, every request after the first is faster.

FastAPI's lifespan context manager makes this clean:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await chess_engine.start()
    yield
    # Shutdown
    await chess_engine.stop()
```

The tradeoff: a single engine instance handles requests sequentially. For a personal coaching tool, that's fine. For hundreds of concurrent users, you'd need multiple engine instances or a job queue.

---

## 5. How Analysis Works

### Single Position Analysis

When you click "Analyze Position," here's the full journey:

1. **Frontend gets the FEN.** FEN (Forsyth-Edwards Notation) is a one-line string that completely describes a chess position - piece placement, whose turn, castling rights, en passant square, move counts.

2. **Frontend POSTs to /api/analyze** with `{"fen": "...", "depth": 15}`.

3. **Backend creates a Board object.** python-chess parses the FEN and validates it. Invalid FEN? 400 error back to the user.

4. **Backend asks Stockfish to analyze.** This is the `engine.analyse(board, Limit(depth=15))` call. Stockfish thinks for 1-2 seconds (at depth 15) and returns its evaluation and best move.

5. **Backend formats the response.** Stockfish gives evaluation in centipawns (hundredths of a pawn). We convert to pawns (divide by 100) because "+0.35" is more intuitive than "+35."

6. **Frontend displays the result.** Color-coded: green for White advantage, red for Black advantage. Shows the evaluation number and the best move in algebraic notation.

### The Evaluation Convention

This tripped us up initially: Stockfish can report evaluation two ways:
- **Relative:** Positive means whoever's turn it is has an advantage
- **White's perspective:** Positive means White has an advantage

The chess world uses White's perspective universally. Chess.com, Lichess, every analysis tool you've seen - positive means White is better, negative means Black is better, regardless of whose turn it is.

We initially used relative evaluation (`.relative`), which meant the same position showed different numbers depending on whose turn it was. Confusing. Switching to `.white()` fixed it.

### Full Game Analysis

Analyzing a complete game is conceptually simple: analyze every position, compare what was played to what was best.

But the details matter:

**For each move:**
1. Analyze the position *before* the move to find the best move and its evaluation
2. Record what move was actually played
3. Analyze the position *after* the move to get the new evaluation
4. Calculate the centipawn loss (how much worse the position got)
5. Classify the move based on that loss

**Classification thresholds:**
| CP Loss | Classification |
|---------|----------------|
| ≤ 0 | Excellent (as good as engine) |
| 1-20 | Good |
| 21-50 | Inaccuracy |
| 51-100 | Mistake |
| > 100 | Blunder |

These match Chess.com and Lichess standards. A blunder means you threw away at least a pawn's worth of advantage (100 centipawns). That feels right - losing a pawn is a blunder in most positions.

**Accuracy calculation:**

We use a simplified formula: `accuracy = 100 - (average_cp_loss / 2)`

Chess.com uses a fancier exponential formula, but this linear version is intuitive and good enough for coaching. An average loss of 20 centipawns per move gives you 90% accuracy. An average loss of 50 gives you 75%. Makes sense.

### Why This Takes Time

A 40-move game has 80 positions to analyze (one before each move). At 1-2 seconds per position, that's 80-160 seconds. For a long game, you might wait 5 minutes.

The loading indicator with progress bar isn't just UI polish - it's essential. Without feedback, users would think the app froze.

Future optimization: analyze at depth 12 instead of 15 for game analysis (roughly half the time for slightly less precision), or run multiple Stockfish instances in parallel.

---

## 6. How Play Mode Works

### The ELO Limiting Trick

Stockfish at full strength is around 3500 ELO. Magnus Carlsen is 2850. To make it useful for practice, we need to weaken it.

Stockfish has built-in options for this:

```python
await self.engine.configure({
    "UCI_LimitStrength": True,
    "UCI_Elo": 1500
})
```

Set `UCI_LimitStrength` to True and Stockfish will intentionally play worse, targeting the specified ELO. It's not perfect - engine play doesn't feel quite like human play at that level - but it's remarkably good for practice.

**The minimum ELO surprise:** We originally planned to support 800-2800 ELO. But when we actually tested, this Stockfish build only goes down to 1350. Different Stockfish versions/builds have different minimums. Always test your assumptions.

### Turn Management

In play mode, the frontend tracks:
- `isPlaying` - Are we in an active game?
- `playerColor` - Are we playing White or Black?
- `isPlayerTurn` - Is it currently our turn?

When you drag a piece:
```javascript
function onDragStart(source, piece, position, orientation) {
    if (isPlaying && !isPlayerTurn) return false;  // Can't move on coach's turn
    if (playerColor === 'white' && piece.search(/^b/) !== -1) return false;  // Can't move Black pieces
    // ... etc
}
```

When you complete a move, we flip `isPlayerTurn` to false and request a coach move. When the coach responds, we apply its move and flip `isPlayerTurn` back to true.

### Why the Backend Is Stateless

The game state lives entirely in the frontend. The backend doesn't know or care that we're playing a game - it just answers "given this position and this ELO, what move?"

This makes the backend simpler:
- No session management
- No game state to persist between requests
- Easy to scale (any server instance can handle any request)

The tradeoff: refresh the page and your game is gone. For an MVP, that's fine. Later, we'll add a database to persist games.

---

## 7. The AI Coach (Claude Integration)

Phase 2 brought the AI coaching layer: you can now have a conversation with Claude about your chess games directly in the interface.

### The Coach Module

The backend gained a new module (`coach.py`) that wraps the Claude API:

```python
class ChessCoach:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    async def chat(self, message, conversation_history, board_context):
        # Build messages with history
        # Inject board context into system prompt
        # Call Claude API
        # Return response
```

The coach is initialized alongside Stockfish when the server starts, using the same lifespan pattern:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await chess_engine.start()
    chess_coach = ChessCoach()  # New
    yield
    await chess_engine.stop()
```

### The Coaching Persona

The system prompt defines how the coach behaves:

- **Patient and Socratic** - Asks questions to understand what the student wants
- **Concrete** - Gives actionable advice, not vague platitudes
- **Board-aware** - Knows the current position and can reference it
- **Honest** - Encouraging but truthful about mistakes

Importantly, the coach does NOT calculate tactics itself. That's Stockfish's job. The coach explains *why* moves are good or bad, guides learning, and helps the student understand concepts.

### Board Context

Every chat message includes the current board state:

```javascript
const boardContext = {
    fen: getCurrentFEN(),      // Current position
    last_move: getLastMove(),  // Most recent move
    mode: getCurrentMode()     // 'play', 'analysis', or 'idle'
};
```

This gets injected into Claude's system prompt, so it knows what position you're looking at. When you ask "Why is this move bad?", Claude can actually see the position you're referring to.

### Conversation State

Like the game state, conversation history lives in the frontend:

```javascript
let conversationHistory = [];

// After each exchange:
conversationHistory.push({ role: 'user', content: message });
conversationHistory.push({ role: 'assistant', content: response });
```

This keeps the backend stateless - any request contains everything needed to continue the conversation. The tradeoff is that refreshing the page loses your chat history (same as the game state).

### The Chat UI

The frontend gained a third column: board | panels | chat. The chat panel includes:

- A scrollable messages area
- User messages (blue, right-aligned)
- Coach messages (gray, left-aligned)
- A "Thinking..." indicator during API calls
- Enter key or button to send

One subtle detail: arrow key shortcuts for navigating moves are disabled when the chat input is focused. Otherwise you'd be jumping through game history while trying to type.

### Why This Architecture

The coach is intentionally separate from Stockfish:

- **Different concerns** - Stockfish calculates; Claude explains
- **Different APIs** - UCI protocol vs. HTTP/JSON
- **Different failure modes** - Stockfish is local and fast; Claude requires network and may be slow

By keeping them separate, each can be tested, scaled, and modified independently. The backend orchestrates them but doesn't mix their responsibilities.

---

## 8. The Data Flow (Updated)

Let's trace two complete user journeys:

### Journey 1: "User loads PGN → clicks Analyze → sees results"

```
1. User clicks "Load PGN" and selects a .pgn file
   ↓
2. Browser reads file, passes text to chessBoard.loadPGN()
   ↓
3. chess.js parses PGN into moves, validates them
   ↓
4. Frontend builds moveHistory array: [{move: "e4", fen: "..."}, ...]
   ↓
5. Board displays starting position, user can navigate with arrows
   ↓
6. User clicks "Analyze Full Game"
   ↓
7. Frontend calls getPGN() to reconstruct the PGN from moveHistory
   ↓
8. POST /api/game/analyze {"pgn": "1. e4 e5...", "depth": 15}
   ↓
9. Backend parses PGN, iterates through all positions
   ↓
10. For each position: Stockfish analyze → classify move → track stats
    ↓
11. Backend returns {moves: [...], summary: {accuracy, mistakes, ...}}
    ↓
12. Frontend displays accuracy percentages and color-coded move list
    ↓
13. User clicks on a blunder in the list
    ↓
14. Board jumps to that position so user can see what happened
```

### Journey 2: "User makes move in play mode → coach responds"

```
1. User is playing as White, it's their turn
   ↓
2. User drags pawn from e2 to e4
   ↓
3. onDragStart checks: isPlaying? isPlayerTurn? own piece? → all yes
   ↓
4. onDrop: chess.js validates move is legal → yes
   ↓
5. chessBoard.makeMove() applies move, updates board visually
   ↓
6. isPlayerTurn = false, status shows "Coach thinking..."
   ↓
7. setTimeout 500ms (for natural feel), then requestCoachMove()
   ↓
8. POST /api/move {"fen": "...", "elo": 1500}
   ↓
9. Backend configures Stockfish to 1500 ELO, asks for a move
   ↓
10. Stockfish returns "e7e5"
    ↓
11. Backend returns {"move": "e7e5", "move_san": "e5", "fen_after": "..."}
    ↓
12. Frontend applies move with chessBoard.makeMove("e7", "e5")
    ↓
13. Frontend checks: game over? No → isPlayerTurn = true
    ↓
14. Status shows "Your turn (White)"
```

### Journey 3: "User asks coach about a position → gets explanation"

```
1. User is looking at a position (maybe after a blunder)
   ↓
2. User types "Why was my last move bad?" in chat input
   ↓
3. User presses Enter or clicks Send
   ↓
4. sendMessage() gathers board context:
   - FEN of current position
   - Last move played
   - Current mode (analysis/play/idle)
   ↓
5. POST /api/chat with message, conversation_history, board_context
   ↓
6. Backend builds Claude messages array from history
   ↓
7. Backend injects board context into system prompt:
   "Current position (FEN): rnbqkb1r/..."
   ↓
8. Claude API call with full context
   ↓
9. Claude analyzes position conceptually and responds:
   "That move lost material because it left your knight undefended..."
   ↓
10. Backend returns {"message": "...", "suggested_action": null}
    ↓
11. Frontend removes "Thinking..." indicator
    ↓
12. Frontend displays coach message (gray, left-aligned)
    ↓
13. Frontend updates conversationHistory array
    ↓
14. User can continue the conversation with follow-up questions
```

---

## 9. Technical Decisions Explained

### WSL as Development Environment

Windows Subsystem for Linux runs a real Linux kernel inside Windows. For this project, that matters because:

- Python chess libraries are Linux-native and work better there
- Stockfish subprocess handling is cleaner on Linux
- Paths and file systems behave predictably
- ML libraries (for future features) have better Linux support

The tradeoff is a slightly more complex setup (VS Code needs the WSL extension), but day-to-day development is smoother.

### The "Two Library" Frontend

Why not use a single library that does both rendering and logic? Because separation of concerns is powerful:

- chessboard.js can be swapped for another rendering library without touching game logic
- chess.js can be updated independently without breaking the visual layer
- Bugs are easier to isolate ("Is it a display bug or a logic bug?")
- Each library does one thing well rather than two things adequately

### Evaluation from White's Perspective

We considered relative evaluation (positive = good for whoever's turn) because it's arguably more intuitive - positive always means "the person about to move is winning."

But the entire chess world uses White's perspective. Every analysis tool, every database, every book. Swimming against that convention would confuse anyone who's used other chess software. And when comparing positions across a game, consistent perspective makes trends clearer.

### Simplified Accuracy Formula

Chess.com uses: `accuracy = 103.1668 * e^(-0.04354 * avg_loss) - 3.1668`

We use: `accuracy = 100 - (avg_loss / 2)`

The exponential formula is more "accurate" in that it matches Chess.com's numbers. But our linear formula:
- Is easier to understand (higher loss = lower accuracy, proportionally)
- Is easier to explain ("you averaged 30 centipawns loss, so about 85% accuracy")
- Is easy to adjust later if needed
- Is good enough for coaching purposes

Premature optimization is the root of all evil. Start simple.

---

## 10. Bugs We Hit and What They Taught Us

### Bug 1: Piece Images Not Rendering

**What went wrong:** The board appeared with an 8x8 grid, but squares showed broken image icons instead of chess pieces.

**How we discovered it:** Opened the page in the browser. Kind of hard to miss.

**Root cause:** chessboard.js's CDN includes the JavaScript and CSS, but not the piece images. The library tries to load images from a path that doesn't exist by default.

**The fix:** Downloaded the Wikipedia piece images locally and configured the `pieceTheme` option to point to them:

```javascript
pieceTheme: 'img/chesspieces/wikipedia/{piece}.png'
```

**The lesson:** CDN-hosted libraries often don't include all assets. When something doesn't render, check what resources it's trying to load (browser dev tools → Network tab).

### Bug 2: python-chess Async API Mismatch

**What went wrong:** Server crashed on startup with a type error about tuples.

**How we discovered it:** Tried to start the FastAPI server.

**Root cause:** The async version of `popen_uci()` returns a tuple `(transport, protocol)`, not just the protocol object. Our code expected just the protocol.

**The fix:**
```python
# Wrong:
self.engine = await chess.engine.popen_uci(self.engine_path)

# Right:
self.transport, self.engine = await chess.engine.popen_uci(self.engine_path)
```

**The lesson:** Async APIs often have different signatures than their sync counterparts. Always check the docs, and read error messages carefully - Python usually tells you exactly what's wrong.

### Bug 3: Evaluation Perspective Confusion

**What went wrong:** The evaluation display showed positive numbers even when Black was clearly winning.

**How we discovered it:** Set up a position where Black had a queen advantage, saw +5.0 displayed.

**Root cause:** Used `.relative` (from side-to-move's perspective) instead of `.white()` (always from White's perspective). In the test position, it was Black's turn, so positive meant "good for Black."

**The fix:**
```python
# Wrong:
score = info['score'].relative

# Right:
score = info['score'].white()
```

**The lesson:** When dealing with chess evaluations, always document whose perspective you're using. It's a common source of bugs.

### Bug 4: Stockfish Minimum ELO Surprise

**What went wrong:** Setting ELO to 800 for a beginner game didn't work - the engine still played strong moves.

**How we discovered it:** Played a game at "800 ELO" and got crushed. Checked Stockfish's actual configuration.

**Root cause:** This build of Stockfish has a minimum UCI_Elo of 1350, not 800. The library clamped our value silently.

**The fix:** Updated the range to 1350-2800 in both backend validation and frontend UI:

```python
elo: int = Field(default=1500, ge=1350, le=2800)
```

**The lesson:** Always test with real values, not just valid ones. And different versions of the same software can have different constraints.

### Bug 5: 100% Accuracy for Both Players

**What went wrong:** After implementing game analysis, every game showed 100% accuracy for both sides.

**How we discovered it:** Analyzed a game where the player clearly blundered multiple times. Both sides showed perfect play.

**Root cause:** The centipawn loss formula had the wrong signs. We were adding where we should subtract:

```python
# Wrong (for White):
cp_loss = eval_before_cp - (-eval_after_cp)

# Right (for White):
cp_loss = eval_before_cp - eval_after_cp
```

**The fix:** Corrected the formulas for both colors:
- White's loss: how much did White's advantage decrease?
- Black's loss: how much did Black's advantage decrease?

**The lesson:** When working with signed values, write out the logic in words before coding. "White's evaluation went from +2.0 to +1.5, so White lost 0.5 pawns of advantage."

### Bug 6: Unresponsive Analyze Button

**What went wrong:** The "Analyze Full Game" button did nothing when clicked. No error, no loading state, nothing.

**How we discovered it:** Clicked the button. Clicked it again. Checked browser console - no errors.

**Root cause:** The JavaScript called `chessBoard.getPGN()`, but that function existed inside the module but wasn't exposed in the public interface return object.

**The fix:** Added `getPGN: getPGN` to the public interface.

**The lesson:** IIFE module pattern requires explicitly exporting everything you want public. Silent failures (no error, just undefined) are particularly sneaky. When a function "doesn't work," first check if it's actually being called.

### Bug 7: Invisible Chessboard

**What went wrong:** After reorganizing the layout to side-by-side columns, the chessboard disappeared.

**How we discovered it:** Opened the page. No board visible (well, tiny and collapsed).

**Root cause:** The board container only had `max-width: 500px` set. When placed in a flex container, chessboard.js needs explicit width and height to render properly.

**The fix:**
```css
#board {
    width: 500px;
    height: 500px;
}
```

**The lesson:** CSS layout changes can have unexpected effects on third-party libraries. When something disappears after layout changes, check the computed dimensions.

---

## 11. Patterns Worth Reusing

### Async Engine Management in Python

The pattern we use for Stockfish could apply to any external process:

```python
class ExternalEngine:
    def __init__(self, path):
        self.path = path
        self.process = None

    async def start(self):
        # Initialize the subprocess

    async def stop(self):
        # Clean shutdown

    async def query(self, request):
        # Send request, get response
```

Combined with FastAPI's lifespan management, you get clean startup/shutdown without global state hacks.

### Frontend State Management Without a Framework

For single-purpose applications, the IIFE module pattern works well:

```javascript
const myModule = (function() {
    // Private state
    let internalState = {};

    // Private functions
    function privateHelper() { }

    // Public API
    return {
        publicMethod: function() {
            // Can access private state
            privateHelper();
        }
    };
})();
```

No build step, no dependencies, clear public/private boundaries. When your app outgrows this, *then* reach for React.

### The "Two-Part Session" Approach

Our development sessions often split: first cleanup/consolidation, then new features. Session 03 spent the first half reorganizing documentation before building play mode.

This is worth formalizing. Technical debt accumulated during rapid feature development should be addressed before adding more features, not indefinitely postponed.

### API Design for Chess Applications

The API surface that emerged is worth noting:

- `POST /api/analyze` - Stateless position analysis
- `POST /api/move` - Stateless move request
- `POST /api/game/analyze` - Stateless game analysis

Everything is stateless. Position comes in, analysis comes out. This makes the API easy to reason about, test, and scale.

---

## 12. What Good Engineering Looks Like Here

### Starting with the Data Layer

We built all the chess analysis capabilities *before* even thinking about the Claude API integration. This might seem backwards - isn't the AI the interesting part?

But the AI coach will need to:
- Get position evaluations
- Analyze games for mistakes
- Play moves at the student's level

Without those capabilities, the AI would be a chat interface with no chess knowledge. By building the data layer first, we have real functionality to integrate with.

### Documentation-Driven Development

Every session starts with a CONTEXT.md (what we know) and TASKS.md (what we're building). Every session ends with a SESSION_SUMMARY.md (what actually happened).

This creates:
- Clear scope for each session
- Institutional memory (why did we make that decision six sessions ago?)
- Onboarding material (where the docs are now)
- A debugging trail (when did that bug get introduced?)

It's more overhead, but for a project that spans multiple sessions with potentially fresh context each time, it's essential.

### Making Decisions Explicit

DECISIONS.md logs every architectural choice with:
- What situation prompted the decision
- What we chose
- Why we chose it over alternatives
- What this enables or constrains

When you wonder "why is it done this way?", the answer is there. No archaeology through old commits needed.

### Building the Simplest Thing That Works

Each feature started minimal:
- Single-position analysis before full-game analysis
- Fixed depth before configurable depth
- No progress bar before progress bar

This isn't laziness - it's testing assumptions. Maybe full-game analysis wouldn't be useful. Maybe depth 15 is always wrong. Build the simple version, use it, *then* add complexity where it's actually needed.

### The Backlog as Pressure Relief

We maintain a BACKLOG.md for "not now, but later" items. When implementing a feature, there's always temptation to also fix that related thing, add that nice-to-have, refactor that ugly code.

Writing it down in the backlog scratches the itch without derailing the current work. The backlog is a parking lot for good ideas that aren't today's priority.

---

## 13. Where This Is Going

**Phase 1 (complete):** Built the data layer - everything needed to analyze chess games and positions.

**Phase 2 (in progress):** The AI coaching layer.
- ✅ Claude API integration with coaching persona
- ✅ Chat interface in the frontend
- ✅ Board context passed to Claude (position, last move, mode)
- ⬜ Claude controlling the board to illustrate points
- ⬜ Lesson plan generation based on game analysis

**Phase 3: Database + Persistence**
- Store analyzed games in PostgreSQL
- User profiles with playing history
- Track accuracy over time
- Build a picture of the player's strengths/weaknesses
- Persistent conversation history

**Phase 4: RAG for Chess Knowledge**
- Embed chess strategy books and articles
- Claude can reference specific passages
- "This is like the technique Capablanca used in..."
- Connect the player's games to chess literature

The architecture continues to pay dividends. The programmatic board API means Claude will eventually be able to set up positions while explaining. The analysis endpoints give Claude evaluations to discuss. The stateless backend pattern extends naturally to the chat endpoint.

---

## 14. Quick Reference

### Running the Project

**Start the backend:**
```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

**Open the frontend:**
Open `src/frontend/chessboard.html` in your browser

**API documentation:**
http://localhost:8000/docs (interactive Swagger UI)

### Key Files

| File | Purpose |
|------|---------|
| `src/frontend/chessboard.html` | The entire frontend application (board + panels + chat) |
| `src/backend/main.py` | FastAPI app, routes, request/response models |
| `src/backend/engine.py` | Stockfish wrapper, analysis logic |
| `src/backend/coach.py` | Claude API wrapper, coaching logic |
| `.env` | API keys (gitignored, never committed) |
| `docs/DECISIONS.md` | Why we made each technical choice |
| `docs/PROGRESS.md` | What was built each session |
| `docs/ARCHITECTURE.md` | System overview diagrams |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Server status check |
| `/api/analyze` | POST | Single position analysis |
| `/api/move` | POST | Get engine move at ELO |
| `/api/game/analyze` | POST | Full game analysis |
| `/api/chat` | POST | Chat with the AI coach |

### Dependencies

**Backend (Python):**
- FastAPI + uvicorn (web server)
- python-chess (Stockfish integration)
- anthropic (Claude API client)
- python-dotenv (environment variable loading)
- Stockfish (system binary at /usr/games/stockfish)

**Frontend (JavaScript):**
- jQuery 3.6.0 (chessboard.js dependency)
- chessboard.js 1.0.0 (board rendering)
- chess.js 0.10.3 (game logic)

**Environment:**
- `.env` file with `ANTHROPIC_API_KEY` (required for chat)

---

*This walkthrough reflects the project as of Session 05 (Phase 2 in progress). You can now have conversations with an AI chess coach that sees your board position. Future sessions will add board control for Claude, lesson generation, database persistence, and RAG capabilities.*
