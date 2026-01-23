# Chess Coach Architecture

**Current State:** Phase 1 - Technical Foundation Complete
**Last Updated:** January 23, 2025

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  chessboard.html                          │  │
│  │                                                           │  │
│  │  • Interactive board UI (chessboard.js)                  │  │
│  │  • Game logic (chess.js)                                 │  │
│  │  • PGN loading & navigation                              │  │
│  │  • Position analysis display                             │  │
│  │  • Programmatic API                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/JSON (CORS enabled)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND (FastAPI)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    REST API Endpoints                     │  │
│  │                                                           │  │
│  │  GET  /api/health    → Server status                    │  │
│  │  POST /api/analyze   → Position analysis                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               ChessEngine Wrapper                         │  │
│  │             (async, persistent engine)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ UCI Protocol (async subprocess)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STOCKFISH ENGINE                               │
│                  (/usr/games/stockfish)                          │
│                                                                  │
│  • Position evaluation (depth 15 default)                       │
│  • Best move calculation                                        │
│  • Mate detection                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Frontend (src/frontend/chessboard.html)

**Single-page HTML application with embedded JavaScript**

**Features:**
- Interactive chessboard (drag-and-drop, click-to-move)
- PGN file loading and move navigation
- Keyboard shortcuts (arrows, home, end)
- Real-time position analysis display
- Color-coded evaluation (green/red for White/Black advantage)
- Mate-in-X detection display

**Libraries:**
- **chessboard.js** 1.0.0 - Board rendering
- **chess.js** 0.10.3 - Game logic, move validation, PGN parsing
- **jQuery** 3.6.0 - Required dependency for chessboard.js

**Public API:**
```javascript
chessBoard.setPosition(fen)
chessBoard.makeMove(from, to, promotion)
chessBoard.loadPGN(pgnString)
chessBoard.getCurrentFEN()
```

---

### 2. Backend (src/backend/)

**FastAPI asynchronous REST API**

**Files:**
- `main.py` - FastAPI app, routes, request/response models
- `engine.py` - Async Stockfish wrapper with lifecycle management
- `requirements.txt` - Python dependencies

**Endpoints:**

**GET /api/health**
- Returns: `{"status": "ok", "engine": "stockfish"}`

**POST /api/analyze**
- Request: `{"fen": "...", "depth": 15}`
- Response: `{"fen": "...", "evaluation": {...}, "best_move": "e2e4", "best_move_san": "e4", "depth": 15}`
- Evaluation types: "cp" (centipawns) or "mate" (mate distance)
- Always from White's perspective: positive = White better, negative = Black better

**Key Features:**
- Async engine management via FastAPI lifespan
- Single persistent Stockfish instance (faster responses)
- CORS middleware for cross-origin requests
- Pydantic models for validation
- Comprehensive error handling (400 for invalid FEN, 500 for engine errors)

---

### 3. Chess Engine (Stockfish)

**System binary at /usr/games/stockfish**

**Communication:**
- UCI (Universal Chess Interface) protocol
- Async subprocess managed by python-chess
- Persistent process (started at server launch, kept alive)

**Analysis Configuration:**
- Default depth: 15 (~1-2 second response time)
- Configurable via API request
- Evaluation always from White's perspective (standard convention)

---

## Data Flow Example

**User clicks "Analyze Position"**

```
1. Browser: Get current FEN from board
   ↓
2. Browser: POST /api/analyze {"fen": "...", "depth": 15}
   ↓
3. Backend: Parse FEN, create chess.Board
   ↓
4. Backend: engine.analyse() → Stockfish via UCI
   ↓
5. Stockfish: Analyzes position, returns evaluation + best move
   ↓
6. Backend: Format response (convert centipawns, UCI to SAN)
   ↓
7. Backend: Return JSON {"evaluation": {...}, "best_move_san": "e4"}
   ↓
8. Browser: Display color-coded evaluation and best move
```

---

## Key Formats

### FEN (Forsyth-Edwards Notation)
```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
└── Position ──┘ └┘ └──┘ └┘ └┘ └┘
                 │   │   │  │  └── Move number
                 │   │   │  └──── Halfmove clock
                 │   │   └────── En passant square
                 │   └────────── Castling rights
                 └────────────── Active color (w/b)
```

### Move Notation
- **UCI:** e2e4, e1g1 (engine format)
- **SAN:** e4, O-O, Nf3 (human-readable)

### Evaluation
- **Centipawn (cp):** +0.35 = White up 0.35 pawns
- **Mate:** M3 = Mate in 3 moves for White, M-2 = Black mates in 2

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | HTML/CSS/JS | ES6+ | User interface |
| Board | chessboard.js | 1.0.0 | Board rendering |
| Logic | chess.js | 0.10.3 | Move validation, PGN |
| Backend | FastAPI | 0.128.0 | REST API server |
| ASGI Server | uvicorn | 0.40.0 | Run FastAPI |
| Chess Library | python-chess | 1.999 | UCI integration |
| Engine | Stockfish | Latest | Position analysis |
| Environment | WSL (Ubuntu) | - | Development |

---

## File Structure

```
chess-coach/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI app & routes
│   │   ├── engine.py            # Stockfish wrapper
│   │   └── requirements.txt     # Python dependencies
│   └── frontend/
│       ├── chessboard.html      # Main application
│       ├── chessboard-1.0.0.min.{css,js}
│       └── img/chesspieces/wikipedia/*.png
│
├── docs/
│   ├── DECISIONS.md             # Architecture decisions
│   ├── PROGRESS.md              # Session summaries
│   ├── ARCHITECTURE.md          # This file
│   ├── incoming/session-XX/     # Session context docs
│   └── outgoing/session-XX/     # Session output docs
│
├── data/samples/                # Sample PGN files
├── venv/                        # Python virtual environment
└── .gitignore
```

---

## Design Principles

1. **Stateless Backend** - Each request is independent; no server-side game state
2. **Frontend Manages State** - Game history, current position, navigation all in browser
3. **Async First** - FastAPI + async python-chess for better performance
4. **Standard Conventions** - Follow chess.com/Lichess standards (White's perspective)
5. **API-Driven** - Programmatic control for future AI integration

---

## Current Capabilities

### ✅ Implemented
- Interactive chessboard with PGN loading
- Move navigation and keyboard shortcuts
- FastAPI backend with Stockfish integration
- Position analysis with evaluation and best move
- Mate-in-X detection
- Color-coded evaluation display
- Error handling and validation

### ⏳ Planned (Next Sessions)
- Play against Stockfish (adjustable ELO)
- Full game analysis (all moves)
- Claude AI coaching integration
- User profiles and game history
- Chess.com/Lichess game import

---

## Performance Characteristics

**Frontend:**
- Load time: < 1s (local files)
- Move response: Instant (client-side)
- PGN load: < 100ms (typical games)

**Backend:**
- Startup: < 1s (engine initialization)
- Analysis (depth 15): ~1-2s per position
- Concurrent requests: Sequential (single engine instance)

---

## Development Workflow

**Start Backend:**
```bash
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
cd src/backend
uvicorn main:app --reload --port 8000
```

**Open Frontend:**
- Open `src/frontend/chessboard.html` in browser
- Or use live server for development

**API Documentation:**
- Auto-generated: http://localhost:8000/docs (FastAPI Swagger UI)

---

## Future Architecture Evolution

### Phase 2: AI Coaching
- Add Claude API integration
- Conversational coaching interface
- Move explanations and suggestions
- Opening repertoire recommendations

### Phase 3: Persistence
- PostgreSQL database
- User profiles and authentication
- Game history storage
- Progress tracking

### Phase 4: Advanced Features
- Game import (Chess.com, Lichess APIs)
- Opening book integration
- Tactical puzzle generation
- Spaced repetition for openings

---

*This is a living document. Update as architecture evolves.*
