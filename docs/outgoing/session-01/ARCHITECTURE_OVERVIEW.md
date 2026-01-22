# Chess Coach Architecture Overview

**Version:** 1.0 (Phase 1)
**Last Updated:** January 22, 2025

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    chessboard.html                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │  UI Layer    │  │  JavaScript  │  │   chessBoard  │  │  │
│  │  │  (HTML/CSS)  │  │   Libraries  │  │   Controller  │  │  │
│  │  │              │  │              │  │               │  │  │
│  │  │ • Board      │  │ • chess.js   │  │ • setPosition │  │  │
│  │  │ • Buttons    │  │ • chessboard │  │ • makeMove    │  │  │
│  │  │ • Info Panel │  │   .js        │  │ • loadPGN     │  │  │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PYTHON BACKEND                               │
│                    (Flask or FastAPI)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      API Layer                            │  │
│  │                                                           │  │
│  │  POST /api/analyze      → Position analysis             │  │
│  │  POST /api/suggest      → Move suggestions              │  │
│  │  POST /api/game/analyze → Full game analysis            │  │
│  │  GET  /api/health       → Health check                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ Python API                        │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Engine Integration Layer                    │  │
│  │                   (python-chess)                          │  │
│  │                                                           │  │
│  │  • Position parsing (FEN)                                │  │
│  │  • Move validation                                       │  │
│  │  • UCI protocol handling                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ UCI Protocol (stdin/stdout)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        STOCKFISH ENGINE                          │
│                      (/usr/games/stockfish)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Analysis Engine                         │  │
│  │                                                           │  │
│  │  • Position evaluation                                   │  │
│  │  • Best move calculation                                 │  │
│  │  • Principal variation                                   │  │
│  │  • Tactical analysis                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (chessboard.html)

**Responsibilities:**
- Display interactive chessboard
- Handle user interactions (drag-drop, button clicks)
- Send analysis requests to backend
- Display analysis results

**Technologies:**
- HTML5 / CSS3
- Vanilla JavaScript (ES6+)
- chessboard.js (board rendering)
- chess.js (move validation, PGN parsing)
- jQuery (chessboard.js dependency)

**Data Flow:**
```
User Action → JavaScript Handler → chessBoard API → Update Display
User Click → Fetch API → Backend → Display Result
```

---

### 2. Backend (To Be Implemented in Session 02)

**Responsibilities:**
- Serve HTTP API endpoints
- Manage Stockfish engine lifecycle
- Parse and validate chess positions
- Format analysis results

**Technologies (Options):**
- **Option A:** Flask + python-chess
  - Simpler, synchronous
  - Good for learning
  - Mature ecosystem

- **Option B:** FastAPI + python-chess
  - Async/await support
  - Modern, faster
  - Auto-generated docs
  - Better for scaling

**Data Flow:**
```
HTTP Request → Route Handler → Engine Manager → Stockfish → Response
```

---

### 3. Chess Engine (Stockfish)

**Responsibilities:**
- Analyze positions
- Calculate best moves
- Provide evaluations
- Find tactics/blunders

**Communication:**
- UCI (Universal Chess Interface) protocol
- Text-based stdin/stdout
- Managed via subprocess

**Data Flow:**
```
position fen [FEN] → go depth 15 → bestmove e2e4 ponder e7e5
```

---

## Data Structures

### FEN (Forsyth-Edwards Notation)
Position representation used throughout the system.

```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
│         │         │ │ │   │ │ │
│         │         │ │ │   │ │ └── Move number
│         │         │ │ │   │ └──── Halfmove clock
│         │         │ │ │   └────── En passant square
│         │         │ │ └────────── Castling rights
│         │         │ └──────────── Active color (w/b)
│         │         └──────────────── Empty squares (8)
│         └──────────────────────────── 2nd-7th ranks
└────────────────────────────────────── 8th rank (Black)
```

### Move Representation

**UCI Format (Stockfish):**
```
e2e4    # Pawn to e4
e7e8q   # Pawn promotes to queen
e1g1    # Kingside castle
```

**SAN Format (chess.js, Display):**
```
e4      # Pawn to e4
e8=Q    # Pawn promotes to queen
O-O     # Kingside castle
Nf3     # Knight to f3
```

### API Request/Response

**Analysis Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15
}
```

**Analysis Response:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "evaluation": {
    "type": "cp",
    "value": 0.25
  },
  "best_move": "e2e4",
  "pv": ["e2e4", "e7e5", "g1f3"],
  "depth": 15
}
```

---

## Current State (Post-Session 01)

### ✅ Implemented
- Frontend: Complete interactive chessboard
- PGN loading and navigation
- Move history management
- Programmatic API (setPosition, makeMove, loadPGN)
- UI with move display and FEN viewer

### ⏳ Pending (Session 02+)
- Python backend
- Stockfish integration
- Analysis API endpoints
- Frontend-backend communication

### 🔮 Future Phases
- Claude API integration
- User profiles and database
- Game import from Chess.com/Lichess
- Coaching conversation interface
- RAG knowledge base

---

## Request Flow Example

### Scenario: User Analyzes Current Position

**Step 1: User Action**
```javascript
// User clicks "Analyze" button (future feature)
const fen = document.getElementById('fenDisplay').textContent;
```

**Step 2: Frontend Request**
```javascript
const response = await fetch('http://localhost:5000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ fen: fen, depth: 15 })
});
```

**Step 3: Backend Processing**
```python
@app.route('/api/analyze', methods=['POST'])
def analyze():
    fen = request.json['fen']
    board = chess.Board(fen)
    info = engine.analyse(board, chess.engine.Limit(depth=15))
    return jsonify({
        'evaluation': info['score'].relative.score() / 100,
        'best_move': str(info['pv'][0])
    })
```

**Step 4: Stockfish Analysis**
```
> position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
> go depth 15
< info depth 15 score cp 32 pv e7e5 g1f3 b8c6
< bestmove e7e5 ponder g1f3
```

**Step 5: Frontend Display**
```javascript
const result = await response.json();
console.log(`Evaluation: +${result.evaluation}`);
console.log(`Best move: ${result.best_move}`);

// Show on page
displayAnalysis(result);
```

---

## File Organization

```
chess-coach/
├── data/
│   └── samples/
│       └── *.pgn                      # Sample games
│
├── docs/
│   ├── CLAUDE_CODE_CONTEXT.md         # Project context
│   ├── DECISIONS.md                   # Architecture log
│   ├── PROGRESS.md                    # Session notes
│   ├── incoming/                      # Context for next session
│   └── outgoing/
│       └── session-01/                # This session's docs
│           ├── SESSION_SUMMARY.md
│           ├── API_REFERENCE.md
│           ├── STOCKFISH_INTEGRATION_GUIDE.md
│           └── ARCHITECTURE_OVERVIEW.md
│
├── src/
│   ├── frontend/
│   │   ├── chessboard.html           # Main app
│   │   ├── chessboard-1.0.0.min.css
│   │   ├── chessboard-1.0.0.min.js
│   │   └── img/
│   │       └── chesspieces/
│   │           └── wikipedia/*.png
│   │
│   └── backend/                       # To be created
│       ├── app.py                     # Flask/FastAPI app
│       ├── engine.py                  # Stockfish wrapper
│       ├── routes/
│       │   └── analyze.py             # API routes
│       └── requirements.txt           # Python dependencies
│
├── tests/                             # Future: Unit tests
├── requirements.txt                   # Python dependencies
└── README.md                          # Project overview
```

---

## Technology Stack

### Current (Phase 1)
| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | HTML/CSS/JS | - | User interface |
| Board Library | chessboard.js | 1.0.0 | Board rendering |
| Chess Logic | chess.js | 0.10.3 | Move validation, PGN |
| Chess Engine | Stockfish | Latest | Position analysis |

### Planned (Phase 2+)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Flask/FastAPI | API server |
| Chess Library | python-chess | UCI integration |
| Database | PostgreSQL | Game storage |
| LLM | Claude API | Coaching conversation |
| Hosting | TBD | Deployment |

---

## Security Considerations

### Current Phase
- ✅ Static HTML file, no server required
- ✅ No user data stored
- ✅ No authentication needed

### Future Phases
- ⚠️ Input validation for FEN strings (prevent injection)
- ⚠️ Rate limiting on API endpoints
- ⚠️ CORS configuration for frontend
- ⚠️ API key management for Claude API
- ⚠️ User authentication for profiles
- ⚠️ Secure storage of game data

---

## Performance Characteristics

### Frontend
- **Load Time:** < 1s (local files)
- **Move Response:** Instant (client-side)
- **PGN Load:** < 100ms for typical games (< 100 moves)
- **Memory:** ~10-20MB

### Backend (Estimated)
- **Analysis (depth 15):** 1-2s per position
- **Analysis (depth 20):** 5-10s per position
- **Concurrent Requests:** 10-20 (single Stockfish instance)
- **Memory:** ~50-100MB per Stockfish process

---

## Scalability Considerations

### Current Architecture (Single User)
- Static HTML file (no scaling needed)
- Single Stockfish instance
- Perfect for personal use

### Future Scaling (If Needed)
- **Multiple Users:** Run multiple Stockfish instances
- **Queue System:** Redis + Celery for async analysis
- **Caching:** Cache analysis results for common positions
- **Load Balancing:** Nginx + multiple backend servers
- **Database:** Connection pooling for PostgreSQL

---

## Error Handling

### Frontend Errors
- Invalid FEN → User-friendly error message
- Network failure → Retry + error display
- Invalid PGN → Parse error with details

### Backend Errors
- Invalid FEN → 400 Bad Request
- Engine failure → 503 Service Unavailable
- Timeout → 504 Gateway Timeout
- Server error → 500 Internal Server Error

### Engine Errors
- Invalid position → Caught by python-chess
- Engine crash → Restart engine automatically
- Timeout → Kill process, return partial results

---

## Testing Strategy

### Frontend Testing
- ✅ Manual testing in browser
- ✅ Console API testing
- Future: Automated tests (Jest, Playwright)

### Backend Testing
- Unit tests (pytest)
- Integration tests (API endpoints)
- Engine communication tests

### End-to-End Testing
- Full flow: Browser → API → Stockfish → Browser
- Test various positions and edge cases
- Performance testing (analysis speed)

---

## Future Architecture Evolution

### Phase 2: AI Coaching Layer
```
Browser ←→ Python Backend ←→ Stockfish
                ↓
           Claude API
                ↓
       Coaching Conversation
```

### Phase 3: Persistent Storage
```
Browser ←→ Python Backend ←→ Stockfish
                ↓           ↑
           Claude API   PostgreSQL
                ↓           ↓
           User Profile   Game History
```

### Phase 4: Game Import
```
Chess.com API ──┐
                ├─→ Python Backend ←→ Browser
Lichess API  ───┘        ↓
                    PostgreSQL
```

---

## Design Principles

1. **Simplicity First**
   - Start with minimal viable features
   - Add complexity only when needed
   - Static file > server when possible

2. **AI as Conductor**
   - Backend controls the board programmatically
   - Board is a "shared whiteboard" for coaching
   - API-first design

3. **User Experience**
   - Instant feedback
   - Clear error messages
   - Keyboard shortcuts
   - Professional UI

4. **Maintainability**
   - Clear code structure
   - Comprehensive documentation
   - Consistent naming conventions
   - Type hints (Python)

5. **Performance**
   - Fast analysis (depth 15 in ~1-2s)
   - Responsive UI (no blocking)
   - Efficient engine usage (reuse process)

---

## Glossary

**FEN:** Forsyth-Edwards Notation - Standard position representation
**UCI:** Universal Chess Interface - Protocol for chess engines
**SAN:** Standard Algebraic Notation - Human-readable move format (e4, Nf3)
**PGN:** Portable Game Notation - Standard format for chess games
**Centipawn (cp):** 1/100th of a pawn - Unit for position evaluation
**Principal Variation (PV):** Best line of play according to engine
**Mate:** Checkmate distance (mate 3 = checkmate in 3 moves)

---

*This document provides a high-level overview of the system architecture. For implementation details, see the specific guides and source code.*
