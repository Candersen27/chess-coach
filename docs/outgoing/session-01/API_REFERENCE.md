# Chessboard API Quick Reference

**Version:** 1.0
**Last Updated:** January 22, 2025

---

## JavaScript API

All functions are accessible via the global `chessBoard` object.

### Position Control

#### `setPosition(fen)`
Set the board to a specific position using FEN notation.

```javascript
// Standard starting position
chessBoard.setPosition("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");

// Empty board
chessBoard.setPosition("8/8/8/8/8/8/8/8 w - - 0 1");

// Custom position (e.g., endgame)
chessBoard.setPosition("8/5k2/8/8/8/8/5K2/8 w - - 0 1");

// Shorthand for starting position
chessBoard.setPosition("start");
```

**Returns:** `true` on success, `false` if FEN is invalid
**Side Effects:** Clears move history, resets to new position
**Errors:** Shows error message if FEN is malformed

---

#### `resetBoard()`
Reset to standard starting position and clear all move history.

```javascript
chessBoard.resetBoard();
```

**Returns:** `undefined`
**Side Effects:** Clears move history, resets to starting position
**Use Case:** Start fresh / clear a loaded game

---

### Move Execution

#### `makeMove(from, to, promotion)`
Programmatically make a move on the board.

```javascript
// Basic move
chessBoard.makeMove("e2", "e4");

// Capture
chessBoard.makeMove("d4", "e5");

// Castling (move the king)
chessBoard.makeMove("e1", "g1");  // White kingside castle

// Pawn promotion (defaults to queen if not specified)
chessBoard.makeMove("e7", "e8");           // Promotes to queen
chessBoard.makeMove("e7", "e8", "n");      // Promotes to knight
```

**Parameters:**
- `from` (string): Starting square (e.g., "e2")
- `to` (string): Destination square (e.g., "e4")
- `promotion` (string, optional): Piece to promote to ('q', 'r', 'b', 'n'). Defaults to 'q'

**Returns:** Move object on success, `null` if move is illegal
**Side Effects:** Updates board position, adds to move history
**Errors:** Shows error message if move is illegal

**Move Object Structure:**
```javascript
{
  color: 'w' or 'b',
  from: 'e2',
  to: 'e4',
  piece: 'p',
  san: 'e4',
  captured: 'p' (if capture),
  promotion: 'q' (if promotion)
}
```

---

### PGN Management

#### `loadPGN(pgnString)`
Load a complete game from PGN format.

```javascript
// Simple PGN
const pgn = `[Event "Casual Game"]
[Site "Chess.com"]
[Date "2025.01.22"]

1. e4 e5 2. Nf3 Nc6 3. Bb5`;

chessBoard.loadPGN(pgn);

// Minimal PGN (just moves)
chessBoard.loadPGN("1. e4 e5 2. Nf3 Nc6");

// From file (use with FileReader API)
document.getElementById('pgnInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.onload = (event) => {
    chessBoard.loadPGN(event.target.result);
  };
  reader.readAsText(file);
});
```

**Parameters:**
- `pgnString` (string): Complete PGN text including headers and moves

**Returns:** `true` on success, `false` if PGN is invalid
**Side Effects:** Resets board, builds move history, sets position to start
**Errors:** Shows error message with details if PGN parsing fails

---

### Navigation

#### `goToStart()`
Jump to the starting position (before any moves).

```javascript
chessBoard.goToStart();
```

**Returns:** `undefined`
**Keyboard Shortcut:** `Home`

---

#### `previousMove()`
Step backward one move in the history.

```javascript
chessBoard.previousMove();
```

**Returns:** `undefined`
**Behavior:** Does nothing if already at start
**Keyboard Shortcut:** `Left Arrow (←)`

---

#### `nextMove()`
Step forward one move in the history.

```javascript
chessBoard.nextMove();
```

**Returns:** `undefined`
**Behavior:** Does nothing if already at end
**Keyboard Shortcut:** `Right Arrow (→)`

---

#### `goToEnd()`
Jump to the final position (after all moves).

```javascript
chessBoard.goToEnd();
```

**Returns:** `undefined`
**Keyboard Shortcut:** `End`

---

### View Controls

#### `flipBoard()`
Rotate the board 180 degrees.

```javascript
chessBoard.flipBoard();
```

**Returns:** `undefined`
**Use Case:** View position from opponent's perspective

---

## Internal State Access

These properties are not directly exposed but can be accessed for debugging:

```javascript
// Access chess.js game object (not recommended for production use)
const game = chessBoard.game;  // Internal - not part of public API

// Get current FEN via DOM
const fen = document.getElementById('fenDisplay').textContent;

// Get current move number via DOM
const moveInfo = document.getElementById('moveNumber').textContent;
```

---

## Common Usage Patterns

### Pattern 1: Demonstrate a Tactic
```javascript
// Reset and show a specific tactical position
chessBoard.resetBoard();
chessBoard.makeMove("e2", "e4");
chessBoard.makeMove("e7", "e5");
chessBoard.makeMove("g1", "f3");
chessBoard.makeMove("b8", "c6");
chessBoard.makeMove("f1", "b5");  // Ruy Lopez
```

### Pattern 2: Set Up an Endgame
```javascript
// King and pawn endgame
chessBoard.setPosition("8/5pk1/8/6P1/8/8/5K2/8 w - - 0 1");
```

### Pattern 3: Load and Navigate a Game
```javascript
// Load a game and jump to a specific move
chessBoard.loadPGN(pgnString);
chessBoard.goToStart();

// Step through move by move
for (let i = 0; i < 10; i++) {
  setTimeout(() => chessBoard.nextMove(), i * 1000);
}
```

### Pattern 4: Analyze a Position
```javascript
// Set position and get FEN for analysis
chessBoard.setPosition("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3");

// Get FEN from display
const fen = document.getElementById('fenDisplay').textContent;

// Send to backend for Stockfish analysis (future feature)
fetch('/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ fen: fen })
})
.then(response => response.json())
.then(data => console.log('Evaluation:', data.evaluation));
```

---

## Event Handling

Currently, the board does not emit custom events, but you can listen to button clicks:

```javascript
// Add custom handler after a move
document.getElementById('nextBtn').addEventListener('click', () => {
  console.log('User advanced to next move');
  // Your custom logic here
});
```

---

## Keyboard Shortcuts

| Key | Action | Function |
|-----|--------|----------|
| `←` | Previous move | `previousMove()` |
| `→` | Next move | `nextMove()` |
| `Home` | Go to start | `goToStart()` |
| `End` | Go to end | `goToEnd()` |

---

## Error Messages

All errors are displayed in the status message area:

```javascript
// Invalid FEN
chessBoard.setPosition("invalid");
// Shows: "Invalid FEN string: [error details]"

// Illegal move
chessBoard.makeMove("e2", "e5");
// Shows: "Invalid move: Illegal move"

// Invalid PGN
chessBoard.loadPGN("not a pgn");
// Shows: "Failed to load PGN: [error details]"
```

---

## Browser Console Testing

Quick tests you can run in the browser console:

```javascript
// Test 1: Position setting
chessBoard.setPosition("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");

// Test 2: Make a series of moves
chessBoard.resetBoard();
["e2-e4", "e7-e5", "g1-f3", "b8-c6"].forEach(m => {
  const [from, to] = m.split('-');
  chessBoard.makeMove(from, to);
});

// Test 3: Navigation
chessBoard.goToStart();
chessBoard.nextMove();
chessBoard.nextMove();
chessBoard.previousMove();

// Test 4: Minimal PGN
chessBoard.loadPGN("1. e4 e5 2. Nf3 Nc6 3. Bb5 a6");
```

---

## Future API Extensions (Not Yet Implemented)

These functions may be added in future sessions:

```javascript
// Potential future additions:
// chessBoard.getPosition()          // Returns current FEN
// chessBoard.getMoveHistory()       // Returns array of all moves
// chessBoard.getCurrentMove()       // Returns current move object
// chessBoard.isGameOver()           // Check if game ended
// chessBoard.getGameResult()        // Get result (1-0, 0-1, 1/2-1/2)
// chessBoard.setHighlight(squares)  // Highlight specific squares
// chessBoard.setArrows(arrows)      // Draw arrows on board
// chessBoard.addEventListener(type, callback)  // Custom event system
```

---

## Integration with Backend (Future)

Example of how this API will be used with the Python backend:

```javascript
// Future: AI coach controls the board
async function coachDemonstrateMove(fen, bestMove) {
  // Set position
  chessBoard.setPosition(fen);

  // Wait for user to see it
  await new Promise(r => setTimeout(r, 1000));

  // Show the best move
  const [from, to] = bestMove.split('-');
  chessBoard.makeMove(from, to);
}

// Future: Send position for analysis
async function analyzeCurrentPosition() {
  const fen = document.getElementById('fenDisplay').textContent;
  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ fen }),
    headers: { 'Content-Type': 'application/json' }
  });
  return await response.json();
}
```

---

## Technical Notes

- **Move Validation:** All moves are validated by chess.js before being applied
- **History Management:** Move history is stored as an array; current position tracked by index
- **Drag-Drop:** Disabled when viewing historical positions (not at end of game)
- **State Synchronization:** Board display and chess.js game state always kept in sync
- **FEN Export:** Current FEN is always displayed in the info panel

---

*For implementation details, see [chessboard.html](../../src/frontend/chessboard.html)*
*For usage examples, see [SESSION_SUMMARY.md](./SESSION_SUMMARY.md)*
