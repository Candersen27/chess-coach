# Session 08 Phase 1: Implementation Tasks

## Overview

This document provides a step-by-step implementation checklist for adding board control to the chess coach. Follow tasks in order for smooth integration.

## Pre-Implementation Checklist

- [ ] Review SESSION_SCOPE.md for goals and deliverables
- [ ] Review TECHNICAL_SPEC.md for API contracts and data structures
- [ ] Review DESIGN_DECISIONS.md for context on approach
- [ ] Ensure current codebase is in working state
- [ ] Test existing functionality (game analysis, play vs coach, chat)

---

## Phase 1: Backend Foundation

### Task 1: Update Stockfish Engine Methods

**File:** `src/backend/engine.py`

**Add these new methods:**

```python
async def get_coaching_context(self, fen: str, depth: int = 15) -> dict:
    """Get comprehensive analysis for coaching feedback."""
    # Implementation in TECHNICAL_SPEC.md
    pass

async def evaluate_move(self, fen: str, move_san: str, depth: int = 15) -> dict:
    """Evaluate a specific move with before/after analysis."""
    # Implementation in TECHNICAL_SPEC.md
    pass
```

**Testing:**
```python
# Test get_coaching_context
result = await engine.get_coaching_context("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(result["top_moves"])  # Should show e4, d4, Nf3, etc.

# Test evaluate_move
result = await engine.evaluate_move(
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "e4"
)
print(result["classification"])  # Should be "excellent" or "good"
```

**Checklist:**
- [ ] Add `get_coaching_context()` method
- [ ] Add `evaluate_move()` method  
- [ ] Test with starting position
- [ ] Test with tactical position (verify it spots tactics)
- [ ] Verify SAN conversion works correctly

---

### Task 2: Add Tool Definition to Coach

**File:** `src/backend/coach.py`

**Define the tool:**

```python
BOARD_CONTROL_TOOL = {
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
                "description": "Position in FEN notation"
            },
            "annotation": {
                "type": "string",
                "description": "Explanation of the position"
            },
            "moves": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional move sequence (leave empty in Phase 1)"
            }
        },
        "required": ["fen", "annotation"]
    }
}
```

**Update system prompt:**

Add board control instructions to the coaching system prompt. See TECHNICAL_SPEC.md for exact text.

**Checklist:**
- [ ] Add `BOARD_CONTROL_TOOL` definition
- [ ] Update system prompt with board control instructions
- [ ] Verify tool schema is valid JSON

---

### Task 3: Implement Tool Calling in Coach

**File:** `src/backend/coach.py`

**Create new function:**

```python
async def chat_with_tools(
    message: str,
    context: dict = None,
    conversation_history: list = None
) -> dict:
    """
    Chat with Claude using tool calling.
    
    Returns:
        {
            "message": "Claude's text response",
            "board_control": {...} or None,
            "tool_calls": [...]
        }
    """
    # Build messages array
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})
    
    # Call Claude API with tools
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[BOARD_CONTROL_TOOL],  # Add tool here
        messages=messages,
        system=build_system_prompt(context)
    )
    
    # Parse response for text and tool calls
    result = {
        "message": "",
        "board_control": None,
        "tool_calls": []
    }
    
    for block in response.content:
        if block.type == "text":
            result["message"] += block.text
        elif block.type == "tool_use" and block.name == "set_board_position":
            result["board_control"] = {
                "fen": block.input["fen"],
                "annotation": block.input["annotation"],
                "moves": block.input.get("moves", [])
            }
            result["tool_calls"].append(block)
    
    return result
```

**Update existing chat function:**

Modify the current `chat()` function to use `chat_with_tools()` instead of direct API call.

**Checklist:**
- [ ] Implement `chat_with_tools()` function
- [ ] Update existing `chat()` to call `chat_with_tools()`
- [ ] Test tool calling works (even without frontend)
- [ ] Verify tool calls are parsed correctly
- [ ] Test fallback when no tool call is made

---

### Task 4: Add Coach Move Endpoint

**File:** `src/backend/main.py`

**Add request model:**

```python
from pydantic import BaseModel

class CoachMoveRequest(BaseModel):
    fen: str
    move: str  # SAN notation
    context: dict = {}
```

**Add route:**

```python
@app.post("/api/coach/move")
async def coach_move_endpoint(request: CoachMoveRequest):
    """Handle user move in Coach Demo mode."""
    # Implementation in TECHNICAL_SPEC.md
    pass
```

**Checklist:**
- [ ] Add `CoachMoveRequest` model
- [ ] Implement `/api/coach/move` route
- [ ] Test with Postman/curl (manual API test)
- [ ] Verify Stockfish analysis is included
- [ ] Verify Claude response includes coaching

**Manual test:**
```bash
curl -X POST http://localhost:8000/api/coach/move \
  -H "Content-Type: application/json" \
  -d '{
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "move": "e4",
    "context": {}
  }'
```

---

### Task 5: Update Chat Endpoint

**File:** `src/backend/main.py`

**Modify `/api/chat` to return board_control:**

```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with AI coach (now with board control)."""
    try:
        response = await coach.chat_with_tools(
            message=request.message,
            context=request.context,
            conversation_history=request.conversation_history
        )
        
        return {
            "message": response["message"],
            "board_control": response.get("board_control"),  # NEW
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "message": "Error occurred",
            "board_control": None,
            "status": "error"
        }
```

**Checklist:**
- [ ] Update response to include `board_control`
- [ ] Test chat endpoint manually
- [ ] Verify backward compatibility (responses without board_control work)

---

## Phase 2: Frontend Implementation

### Task 6: Add Mode Toggle UI

**File:** `src/frontend/chessboard.html`

**Add HTML (in board panel section):**

```html
<!-- Add before the chessboard div -->
<div class="mode-toggle">
    <button id="myGameMode" class="mode-btn active" onclick="switchToMyGame()">
        📋 My Game
    </button>
    <button id="coachDemoMode" class="mode-btn" onclick="switchToCoachDemo()">
        🎓 Coach Demo
    </button>
</div>
```

**Add CSS:**

```css
.mode-toggle {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
}

.mode-btn {
    flex: 1;
    padding: 8px 16px;
    border: 2px solid #ccc;
    background: white;
    cursor: pointer;
    border-radius: 4px;
    font-size: 14px;
    transition: all 0.2s;
}

.mode-btn.active {
    background: #4CAF50;
    color: white;
    border-color: #4CAF50;
}

.mode-btn:hover:not(.active) {
    background: #f0f0f0;
}
```

**Checklist:**
- [ ] Add mode toggle HTML
- [ ] Add CSS styling
- [ ] Verify buttons are visible and styled correctly

---

### Task 7: Implement Game State Management

**File:** `src/frontend/chessboard.html`

**Add state object:**

```javascript
const gameState = {
    myGame: {
        pgn: "",
        currentMove: 0,
        analysis: {},
        fen: ""
    },
    coachDemo: {
        pgn: "",
        currentMove: 0,
        positions: [],
        fen: "",
        isInteractive: true
    },
    activeMode: "myGame",
    isWaitingForCoach: false,
    lastMove: null
};
```

**Implement mode switching:**

```javascript
function switchToCoachDemo(boardControl) {
    // Implementation in TECHNICAL_SPEC.md
}

function switchToMyGame() {
    // Implementation in TECHNICAL_SPEC.md
}

function enableInteractiveMode() {
    // Make board draggable
}

function disableInteractiveMode() {
    // Make board view-only
}
```

**Checklist:**
- [ ] Add `gameState` object
- [ ] Implement `switchToCoachDemo()`
- [ ] Implement `switchToMyGame()`
- [ ] Implement `enableInteractiveMode()`
- [ ] Implement `disableInteractiveMode()`
- [ ] Test mode switching preserves state

---

### Task 8: Add PGN Generation

**File:** `src/frontend/chessboard.html`

**Implement function:**

```javascript
function buildPGNFromFEN(fen, moves = []) {
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

**Test:**

```javascript
// Test with starting position
const pgn = buildPGNFromFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
console.log(pgn);

// Test loading it
loadPGN(pgn);
// Board should show starting position
```

**Checklist:**
- [ ] Implement `buildPGNFromFEN()`
- [ ] Test PGN generation
- [ ] Verify chess.js loads PGN correctly
- [ ] Test with mid-game position

---

### Task 9: Update Chat Handler for Board Control

**File:** `src/frontend/chessboard.html`

**Modify `sendMessage()` function:**

```javascript
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    input.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: message,
                context: {
                    pattern_analysis: patternAnalysis,
                    conversation_history: conversationHistory
                }
            })
        });
        
        const data = await response.json();
        
        // Add text response
        addMessage('assistant', data.message);
        
        // Handle board control if present
        if (data.board_control) {
            switchToCoachDemo(data.board_control);
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('system', 'Error: Could not send message');
    }
}
```

**Checklist:**
- [ ] Update `sendMessage()` to check for `board_control`
- [ ] Call `switchToCoachDemo()` when board control is present
- [ ] Test by asking "Show me the starting position"
- [ ] Verify board updates correctly

---

### Task 10: Implement Interactive Moves

**File:** `src/frontend/chessboard.html`

**Update `onDrop()` function:**

```javascript
function onDrop(source, target) {
    // Check active mode
    if (gameState.activeMode === "myGame") {
        return 'snapback';  // View-only
    }
    
    // Coach Demo - allow moves
    const move = game.move({
        from: source,
        to: target,
        promotion: 'q'
    });
    
    if (move === null) {
        return 'snapback';  // Illegal
    }
    
    board.position(game.fen());
    handleUserMove(move.san);
}

async function handleUserMove(moveSan) {
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
                    conversation_history: conversationHistory
                }
            })
        });
        
        const data = await response.json();
        addMessage('assistant', data.message);
        
        if (data.board_control) {
            switchToCoachDemo(data.board_control);
        }
        
    } catch (error) {
        console.error('Move error:', error);
        addMessage('system', 'Error analyzing move');
    } finally {
        gameState.isWaitingForCoach = false;
        hideCoachThinking();
    }
}
```

**Add loading indicators:**

```javascript
function showCoachThinking() {
    const indicator = document.createElement('div');
    indicator.id = 'coach-thinking';
    indicator.className = 'coach-thinking';
    indicator.innerHTML = '🤔 Coach is analyzing...';
    document.getElementById('chat-messages').appendChild(indicator);
}

function hideCoachThinking() {
    const el = document.getElementById('coach-thinking');
    if (el) el.remove();
}
```

**Checklist:**
- [ ] Update `onDrop()` to check mode
- [ ] Implement `handleUserMove()`
- [ ] Add loading indicators
- [ ] Test making moves in Coach Demo mode
- [ ] Verify moves in My Game mode are blocked
- [ ] Test illegal moves return snapback

---

## Phase 3: Integration Testing

### Task 11: End-to-End Testing

**Test Scenario 1: Claude Demonstrates Position**

1. [ ] Load the application
2. [ ] In chat, type: "Show me a knight fork position"
3. [ ] Verify Claude responds with text
4. [ ] Verify board switches to Coach Demo mode
5. [ ] Verify position loads on board
6. [ ] Verify annotation displays
7. [ ] Verify mode button shows "Coach Demo" as active

**Test Scenario 2: User Explores Position**

1. [ ] With Coach Demo active, try to move a piece
2. [ ] Verify move is allowed (piece moves)
3. [ ] Verify "Coach is thinking..." appears
4. [ ] Verify Claude responds with analysis
5. [ ] Verify Stockfish classification is reasonable

**Test Scenario 3: Mode Switching**

1. [ ] Load a game in My Game mode
2. [ ] Navigate to move 5
3. [ ] Ask Claude to show a position (switches to Coach Demo)
4. [ ] Click "My Game" button
5. [ ] Verify original game is restored
6. [ ] Verify still on move 5
7. [ ] Switch back to Coach Demo
8. [ ] Verify Coach Demo position is preserved

**Test Scenario 4: Navigation in Coach Demo**

1. [ ] Claude shows a position
2. [ ] User makes move A
3. [ ] Claude shows resulting position
4. [ ] User makes move B
5. [ ] Click ← button
6. [ ] Verify board goes back to after move A
7. [ ] Click ← again
8. [ ] Verify board goes back to original position
9. [ ] Click → to navigate forward

**Checklist:**
- [ ] Test Scenario 1 passes
- [ ] Test Scenario 2 passes
- [ ] Test Scenario 3 passes
- [ ] Test Scenario 4 passes
- [ ] No console errors during testing
- [ ] All mode transitions are smooth
- [ ] Board always displays correct position

---

### Task 12: Edge Case Testing

**Test illegal moves:**
- [ ] Try moving opponent's piece (should snapback)
- [ ] Try moving to invalid square (should snapback)
- [ ] Try moving pinned piece illegally (should snapback)

**Test API error handling:**
- [ ] Stop backend, try to send move (should show error)
- [ ] Send invalid FEN (should handle gracefully)
- [ ] Send invalid move notation (should handle gracefully)

**Test mode edge cases:**
- [ ] Switch modes rapidly (no crashes)
- [ ] Switch modes while "thinking" indicator is showing
- [ ] Load new game while in Coach Demo mode

**Checklist:**
- [ ] All illegal moves handled correctly
- [ ] API errors show user-friendly messages
- [ ] No crashes during edge cases
- [ ] State management is robust

---

## Phase 4: Documentation

### Task 13: Update Project Documentation

**Files to update:**

1. [ ] `docs/PROGRESS.md` - Add Session 08 entry
2. [ ] `docs/ARCHITECTURE.md` - Document board control system
3. [ ] `docs/DECISIONS.md` - Add decisions from DESIGN_DECISIONS.md
4. [ ] `docs/outgoing/session-08/SESSION_SUMMARY.md` - Create summary

**Session summary should include:**
- What was built
- What works
- What doesn't work (known issues)
- What's next (Phase 2 features)
- Any tech debt or refactoring needs

**Checklist:**
- [ ] PROGRESS.md updated
- [ ] ARCHITECTURE.md updated
- [ ] DECISIONS.md updated
- [ ] SESSION_SUMMARY.md created

---

## Task 14: Code Cleanup

**Before finalizing:**

- [ ] Remove debug console.log statements
- [ ] Add comments to complex functions
- [ ] Ensure consistent code style
- [ ] Remove unused variables/functions
- [ ] Update any hardcoded values

**Final checklist:**
- [ ] All TODOs resolved or documented
- [ ] No linter errors
- [ ] Code is readable and well-commented
- [ ] Git commits are clean and descriptive

---

## Success Criteria Verification

Before marking Session 08 Phase 1 as complete, verify:

- [ ] ✅ User can ask Claude to show a position → board updates
- [ ] ✅ User can make moves in Coach Demo mode → Claude responds
- [ ] ✅ User can switch between their game and coach demonstrations
- [ ] ✅ Navigation (← →) works for both modes
- [ ] ✅ Claude's coaching includes Stockfish tactical accuracy
- [ ] ✅ No critical bugs or crashes
- [ ] ✅ Documentation is updated

**The real test:**
- [ ] You can analyze your own game and ask Claude to demonstrate alternatives
- [ ] You can explore positions interactively and Claude provides intelligent coaching
- [ ] The experience feels natural and helpful

---

## Common Issues & Troubleshooting

### Issue: Tool calls not working
- Check Claude API key is valid
- Verify tools array is passed to API call
- Check tool schema is valid JSON
- Look for errors in response parsing

### Issue: Board not updating
- Check `board_control` is in API response
- Verify `switchToCoachDemo()` is being called
- Check PGN is valid with FEN header
- Verify chess.js can load the PGN

### Issue: Moves not working in Coach Demo
- Check `gameState.activeMode` is "coachDemo"
- Verify `onDrop()` is checking mode correctly
- Check draggable is enabled for the board
- Look for JavaScript errors in console

### Issue: State not preserved when switching modes
- Verify `gameState` is being updated correctly
- Check mode switch functions save state before switching
- Ensure currentMove index is saved/restored

---

*Implementation tasks for Session 08 Phase 1 - February 11, 2026*
