# Session 08 Phase 1: Technical Specification

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  My Game     │         │ Coach Demo   │         │
│  │  Mode        │◄───────►│ Mode         │         │
│  │  (view-only) │         │ (interactive)│         │
│  └──────────────┘         └──────────────┘         │
│         │                        │                   │
│         └────────┬───────────────┘                   │
│                  ▼                                    │
│          [Chessboard UI]                             │
│          ← → navigation                              │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              Backend API                             │
│                                                      │
│  POST /api/chat (MODIFIED)                          │
│  ├─► Claude API (with tools)                        │
│  │   └─► Returns: text + optional tool_use          │
│  └─► Parse response                                  │
│      ├─► Extract text for chat                       │
│      └─► Extract board control for frontend          │
│                                                      │
│  POST /api/coach/move  [NEW ENDPOINT]               │
│  ├─► Validate move with chess.js                    │
│  ├─► Stockfish: eval before/after, top moves        │
│  └─► Claude API (with Stockfish context)            │
│      └─► Returns coaching response                   │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
            ┌──────────────┐
            │  Stockfish   │
            │  Engine      │
            └──────────────┘
```

## Claude Tool Definition

### Tool: set_board_position

```python
{
    "name": "set_board_position",
    "description": """Display a chess position on the board to demonstrate a concept, 
                      show a position from the user's games, or illustrate a teaching point.
                      The position will be loaded in Coach Demo mode where the user can 
                      interact with it.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "fen": {
                "type": "string",
                "description": "Position in Forsyth-Edwards Notation (FEN). Example: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'"
            },
            "annotation": {
                "type": "string",
                "description": "Explanation of what to notice about this position, what the key idea is, or what the user should try"
            },
            "moves": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: Sequence of moves in Standard Algebraic Notation to demonstrate from this position (e.g., ['Nf6', 'Nc3', 'd5']). Phase 1: Leave empty - single positions only."
            }
        },
        "required": ["fen", "annotation"]
    }
}
```

### System Prompt Addition

Add to Claude's system prompt in `coach.py`:

```
BOARD CONTROL CAPABILITY:

You have the ability to control the chessboard during coaching conversations. 
Use the set_board_position tool to:
- Show positions from the user's games
- Demonstrate tactical patterns
- Illustrate strategic concepts
- Display positions from lesson plans
- Show consequences of moves

When you use this tool, the board will update in the user interface and switch 
to Coach Demo mode. The user can then interact with the position by making moves, 
and you'll receive those moves along with Stockfish analysis to provide coaching.

The user can navigate through positions you've shown using ← → buttons.

IMPORTANT: In Phase 1, leave the 'moves' array empty - only set positions, don't demonstrate sequences yet.
```

## API Contracts

### POST /api/chat (Modified)

**Request:**
```json
{
    "message": "Show me the knight fork from my game 3",
    "context": {
        "pattern_analysis": {...},
        "conversation_history": [...]
    }
}
```

**Response (with board control):**
```json
{
    "message": "Here's that position from move 15. Notice how the knight on d4 attacks both the king and rook.",
    "board_control": {
        "fen": "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 1",
        "annotation": "White's knight forks king and rook",
        "moves": []
    }
}
```

**Response (without board control):**
```json
{
    "message": "That's a great question about pawn structure...",
    "board_control": null
}
```

### POST /api/coach/move (New Endpoint)

**Purpose:** Handle user moves in Coach Demo mode, get Stockfish analysis, and return Claude's coaching response.

**Request:**
```json
{
    "fen": "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 1",
    "move": "Nf6",
    "context": {
        "conversation_history": [...],
        "current_demonstration": "knight fork pattern",
        "user_patterns": {...}
    }
}
```

**Response:**
```json
{
    "message": "Good! You're developing and defending. But now I can play Nxe5...",
    "board_control": {
        "fen": "rnbqkb1r/pp2pppp/3p1n2/4N3/4P3/8/PPP2PPP/RNBQKB1R b KQkq - 0 1",
        "annotation": "After Nxe5, White threatens the d6 pawn",
        "moves": []
    },
    "stockfish_eval": {
        "eval_before": 0.3,
        "eval_after": 0.8,
        "classification": "good",
        "best_move": {
            "san": "Nf6",
            "eval": 0.8
        },
        "alternative_moves": [
            {"san": "Nf6", "eval": 0.8},
            {"san": "d4", "eval": 0.5},
            {"san": "Nc6", "eval": 0.3}
        ]
    }
}
```

## Frontend State Management

### Game State Structure

```javascript
const gameState = {
    // My Game mode state
    myGame: {
        pgn: "",              // Original uploaded PGN
        currentMove: 0,        // Current position in navigation
        analysis: {},          // Stockfish analysis if available
        fen: ""               // Current FEN in this mode
    },
    
    // Coach Demo mode state
    coachDemo: {
        pgn: "",              // PGN built from Claude's tool calls
        currentMove: 0,        // Current position in navigation
        positions: [],         // History of shown positions [{fen, annotation}, ...]
        fen: "",              // Current FEN in this mode
        isInteractive: true    // Always true in Phase 1
    },
    
    // Active mode
    activeMode: "myGame",  // "myGame" or "coachDemo"
    
    // UI state
    isWaitingForCoach: false,
    lastMove: null
};
```

### Mode Switching Functions

```javascript
function switchToCoachDemo(boardControl) {
    // 1. Save current My Game state
    if (gameState.activeMode === "myGame") {
        gameState.myGame.currentMove = currentMoveIndex;
        gameState.myGame.fen = game.fen();
    }
    
    // 2. Build Coach Demo PGN from board control
    const pgn = buildPGNFromFEN(boardControl.fen, boardControl.moves);
    gameState.coachDemo.pgn = pgn;
    gameState.coachDemo.positions.push(boardControl);
    gameState.coachDemo.fen = boardControl.fen;
    
    // 3. Switch mode
    gameState.activeMode = "coachDemo";
    
    // 4. Update UI
    document.getElementById('myGameMode').classList.remove('active');
    document.getElementById('coachDemoMode').classList.add('active');
    
    loadPGN(pgn);
    showAnnotation(boardControl.annotation);
    enableInteractiveMode();
}

function switchToMyGame() {
    // 1. Switch mode
    gameState.activeMode = "myGame";
    
    // 2. Restore My Game state
    loadPGN(gameState.myGame.pgn);
    jumpToMove(gameState.myGame.currentMove);
    
    // 3. Update UI
    document.getElementById('coachDemoMode').classList.remove('active');
    document.getElementById('myGameMode').classList.add('active');
    
    disableInteractiveMode();
}

function enableInteractiveMode() {
    // Make board draggable in Coach Demo
    board = Chessboard('board', {
        ...config,
        draggable: true,
        onDrop: onDropCoachDemo
    });
}

function disableInteractiveMode() {
    // Make board view-only in My Game
    board = Chessboard('board', {
        ...config,
        draggable: false
    });
}
```

## PGN Generation with FEN Headers

### Python Implementation

```python
# In src/backend/coach.py or new utils file

def build_coach_demo_pgn(fen: str, moves: list = None, annotation: str = "") -> str:
    """
    Build a PGN string with custom starting position.
    
    Args:
        fen: Starting position in FEN notation
        moves: Optional list of moves in SAN (Phase 1: always empty or None)
        annotation: Position explanation
    
    Returns:
        Valid PGN string with FEN header
    """
    pgn_parts = [
        '[Event "Coach Demonstration"]',
        '[Site "AI Chess Coach"]',
        '[Date "????.??.??"]',
        '[Round "?"]',
        '[White "Student"]',
        '[Black "Coach"]',
        '[Result "*"]',
        f'[FEN "{fen}"]',
        '[SetUp "1"]',  # Required when FEN is present
        ''
    ]
    
    if annotation:
        # Add annotation as comment
        pgn_parts.append(f'{{ {annotation} }}')
        pgn_parts.append('')
    
    # Phase 1: moves will be empty, but structure is ready for Phase 2
    if moves and len(moves) > 0:
        move_text = format_moves_for_pgn(moves, fen)
        pgn_parts.append(move_text)
    
    pgn_parts.append('*')  # Game in progress
    
    return '\n'.join(pgn_parts)


def format_moves_for_pgn(moves: list, starting_fen: str) -> str:
    """
    Format moves with proper numbering based on starting position.
    
    Phase 1: Not used (moves array is empty)
    Phase 2: Will enable move sequences
    """
    # Parse FEN to get move number and side to move
    fen_parts = starting_fen.split()
    side_to_move = fen_parts[1]  # 'w' or 'b'
    move_number = int(fen_parts[-1])
    
    result = []
    current_move_num = move_number
    is_white_move = (side_to_move == 'w')
    
    for i, move in enumerate(moves):
        if is_white_move:
            result.append(f"{current_move_num}. {move}")
        else:
            if i == 0:
                result.append(f"{current_move_num}... {move}")
            else:
                result.append(move)
        
        if not is_white_move:
            current_move_num += 1
        is_white_move = not is_white_move
    
    return ' '.join(result)
```

### JavaScript Implementation

```javascript
// In chessboard.html

function buildPGNFromFEN(fen, moves = []) {
    // Phase 1: moves will always be empty
    const pgnLines = [
        '[Event "Coach Demonstration"]',
        '[Site "AI Chess Coach"]',
        '[FEN "' + fen + '"]',
        '[SetUp "1"]',
        '',
        '*'
    ];
    
    return pgnLines.join('\n');
}
```

## Stockfish Integration for Coaching

### New Engine Methods

Add these methods to `src/backend/engine.py`:

```python
async def get_coaching_context(self, fen: str, depth: int = 15) -> dict:
    """
    Get comprehensive analysis for coaching feedback.
    
    Args:
        fen: Position in FEN notation
        depth: Search depth (default 15 for balance of speed/accuracy)
    
    Returns:
        {
            "evaluation": 0.5,  # Evaluation in pawns
            "top_moves": [
                {"move": "e2e4", "san": "e4", "eval": 0.5},
                {"move": "d2d4", "san": "d4", "eval": 0.3},
                {"move": "g1f3", "san": "Nf3", "eval": 0.2}
            ],
            "mate_in": None  # or integer if mate found
        }
    """
    # Set position
    self.engine.set_fen_position(fen)
    
    # Get top 3 moves
    top_moves = self.engine.get_top_moves(num_top_moves=3)
    
    # Get evaluation
    evaluation = self.engine.get_evaluation()
    
    # Create chess.Board for SAN conversion
    board = chess.Board(fen)
    
    # Format for coaching
    result = {
        "evaluation": evaluation['value'] / 100,  # Convert centipawns to pawns
        "top_moves": [],
        "mate_in": evaluation.get('mate')
    }
    
    # Parse and include top moves with SAN notation
    for move_data in top_moves[:3]:
        move_uci = move_data['Move']
        move_obj = chess.Move.from_uci(move_uci)
        san = board.san(move_obj)
        
        result["top_moves"].append({
            "move": move_uci,
            "san": san,
            "eval": move_data.get('Centipawn', 0) / 100
        })
    
    return result


async def evaluate_move(self, fen: str, move_san: str, depth: int = 15) -> dict:
    """
    Evaluate a specific move and get before/after analysis.
    
    Args:
        fen: Position before the move
        move_san: Move in Standard Algebraic Notation (e.g., "Nf6")
        depth: Search depth
    
    Returns:
        {
            "eval_before": 0.3,
            "eval_after": 0.8,
            "classification": "good",  # excellent/good/inaccuracy/mistake/blunder
            "best_move": {"san": "Nf3", "eval": 0.9},
            "alternative_moves": [...]
        }
    """
    # Get position before move
    context_before = await self.get_coaching_context(fen, depth)
    
    # Apply move to get new position
    board = chess.Board(fen)
    try:
        move = board.parse_san(move_san)
        board.push(move)
    except ValueError as e:
        raise ValueError(f"Invalid move {move_san}: {e}")
    
    # Get position after move
    context_after = await self.get_coaching_context(board.fen(), depth)
    
    # Classify move quality using existing thresholds
    # From White's perspective
    eval_before = context_before["evaluation"]
    eval_after = -context_after["evaluation"]  # Flip sign (it's opponent's turn now)
    eval_loss = eval_before - eval_after
    
    # Use same thresholds as game analysis
    if eval_loss <= 0.2:
        classification = "excellent"
    elif eval_loss <= 0.5:
        classification = "good"
    elif eval_loss <= 1.0:
        classification = "inaccuracy"
    elif eval_loss <= 2.0:
        classification = "mistake"
    else:
        classification = "blunder"
    
    return {
        "eval_before": eval_before,
        "eval_after": eval_after,
        "eval_loss": eval_loss,
        "classification": classification,
        "best_move": context_before["top_moves"][0] if context_before["top_moves"] else None,
        "alternative_moves": context_before["top_moves"]
    }
```

## Backend Route Implementations

### Modified /api/chat Route

```python
# In src/backend/main.py

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat with AI coach (now with board control via tools).
    """
    try:
        response = await coach.chat_with_tools(
            message=request.message,
            context=request.context,
            conversation_history=request.conversation_history
        )
        
        return {
            "message": response["message"],
            "board_control": response.get("board_control"),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "message": "I encountered an error. Please try again.",
            "board_control": None,
            "status": "error",
            "error": str(e)
        }
```

### New /api/coach/move Route

```python
# In src/backend/main.py

from pydantic import BaseModel

class CoachMoveRequest(BaseModel):
    fen: str
    move: str  # SAN notation
    context: dict = {}

@app.post("/api/coach/move")
async def coach_move_endpoint(request: CoachMoveRequest):
    """
    Handle user move in Coach Demo mode.
    Returns coaching response with Stockfish analysis.
    """
    try:
        # Get Stockfish analysis first
        engine = get_engine()
        move_analysis = await engine.evaluate_move(
            fen=request.fen,
            move_san=request.move,
            depth=15
        )
        
        # Build coaching prompt with Stockfish context
        coaching_prompt = f"""
The user just played: {request.move}

Stockfish analysis:
- Evaluation before: {move_analysis['eval_before']:.2f}
- Evaluation after: {move_analysis['eval_after']:.2f}
- Evaluation loss: {move_analysis['eval_loss']:.2f}
- Move classification: {move_analysis['classification']}
- Best move was: {move_analysis['best_move']['san']} ({move_analysis['best_move']['eval']:.2f})

Current context: {request.context.get('current_demonstration', 'General coaching')}

Provide coaching feedback. If this is a mistake or blunder, use set_board_position 
to show the consequences or demonstrate better alternatives.
"""
        
        # Get Claude response with tool calling
        response = await coach.chat_with_tools(
            message=coaching_prompt,
            context=request.context,
            conversation_history=request.context.get('conversation_history', [])
        )
        
        return {
            "message": response["message"],
            "board_control": response.get("board_control"),
            "stockfish_eval": move_analysis,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Coach move error: {e}")
        return {
            "message": "I encountered an error analyzing your move. Please try again.",
            "board_control": None,
            "stockfish_eval": None,
            "status": "error",
            "error": str(e)
        }
```

## Frontend Interactive Move Handling

### Modified onDrop Function

```javascript
// In chessboard.html

function onDrop(source, target) {
    // Check active mode
    if (gameState.activeMode === "myGame") {
        // My Game mode is view-only
        return 'snapback';
    }
    
    // Coach Demo mode - allow moves
    const move = game.move({
        from: source,
        to: target,
        promotion: 'q'  // Always promote to queen for simplicity
    });
    
    if (move === null) {
        return 'snapback';  // Illegal move
    }
    
    // Update board
    board.position(game.fen());
    
    // Send move to coach
    handleUserMove(move.san);
    
    return true;
}

async function handleUserMove(moveSan) {
    // Show loading state
    gameState.isWaitingForCoach = true;
    showCoachThinking();
    
    try {
        const response = await fetch('/api/coach/move', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                fen: game.fen(),
                move: moveSan,
                context: {
                    conversation_history: conversationHistory,
                    current_demonstration: currentDemonstration,
                    user_patterns: patternAnalysis
                }
            })
        });
        
        const data = await response.json();
        
        // Add coach response to chat
        addMessage('assistant', data.message);
        
        // Update board if coach demonstrates new position
        if (data.board_control) {
            switchToCoachDemo(data.board_control);
        }
        
        // Store Stockfish eval for debugging/display
        if (data.stockfish_eval) {
            console.log('Move evaluation:', data.stockfish_eval);
            // Could display this in UI: "That move was: [classification]"
        }
        
    } catch (error) {
        console.error('Error sending move to coach:', error);
        addMessage('system', 'Error communicating with coach. Please try again.');
    } finally {
        gameState.isWaitingForCoach = false;
        hideCoachThinking();
    }
}

function showCoachThinking() {
    // Add thinking indicator to UI
    const indicator = document.createElement('div');
    indicator.id = 'coach-thinking';
    indicator.className = 'coach-thinking';
    indicator.innerHTML = '🤔 Coach is analyzing...';
    document.getElementById('chat-messages').appendChild(indicator);
}

function hideCoachThinking() {
    const indicator = document.getElementById('coach-thinking');
    if (indicator) {
        indicator.remove();
    }
}
```

## Data Flow Summary

### Scenario 1: Claude Demonstrates Position

```
1. User: "Show me the knight fork from game 3"
2. POST /api/chat → coach.py
3. Claude calls set_board_position tool
4. coach.py returns: {message: "Here's...", board_control: {fen, annotation}}
5. Frontend receives response
6. switchToCoachDemo(board_control)
7. buildPGNFromFEN(fen) → loads on board
8. Board updates, mode switches to Coach Demo
```

### Scenario 2: User Makes Move in Coach Demo

```
1. User drags piece (e.g., Nf6)
2. onDrop validates → legal move
3. POST /api/coach/move with {fen, move, context}
4. Backend: engine.evaluate_move(fen, "Nf6")
5. Backend: coach.chat_with_tools(with Stockfish data)
6. Claude analyzes, possibly calls set_board_position
7. Backend returns: {message, board_control, stockfish_eval}
8. Frontend: displays message, updates board if board_control present
```

---

## Testing Checklist

- [ ] Claude can call set_board_position tool successfully
- [ ] Board updates when tool call is received
- [ ] Mode toggle works (My Game ↔ Coach Demo)
- [ ] State preservation when switching modes
- [ ] PGN with FEN header loads correctly
- [ ] User can make moves in Coach Demo mode
- [ ] Moves are illegal → snapback works
- [ ] /api/coach/move returns correct Stockfish analysis
- [ ] Claude receives Stockfish context and coaches appropriately
- [ ] Navigation (← →) works in both modes
- [ ] Annotations display correctly

---

*Technical specification for Session 08 Phase 1 - February 11, 2026*
