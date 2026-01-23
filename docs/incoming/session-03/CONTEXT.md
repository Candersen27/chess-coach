# Session 03 Context - Play vs Coach Mode

> **Date:** January 23, 2025
> **Phase:** Phase 1 - Technical Foundation
> **Session Goal:** (1) Clean up docs structure, (2) Build play-vs-coach mode with ELO calibration

---

## What Exists (Session 02 Complete)

### Backend
- `src/backend/main.py` — FastAPI app with CORS, lifespan management
- `src/backend/engine.py` — Async Stockfish wrapper
- `src/backend/requirements.txt` — Dependencies installed in venv
- Endpoints: `GET /api/health`, `POST /api/analyze`

### Frontend
- `src/frontend/chessboard.html` — Interactive board with:
  - PGN loading and navigation
  - "Analyze Position" button
  - Color-coded evaluation display
  - Best move display

### Infrastructure
- Python venv at project root
- Git repo on GitHub (committed through Session 02)
- Stockfish at `/usr/games/stockfish`

---

## Session 03 Has Two Parts

### Part A: Documentation Cleanup (STOP FOR COMMIT AFTER)

The current docs structure is messy. Clean it up before building new features.

**Current (messy):**
```
docs/
├── CLAUDE_CODE_CONTEXT.md    # Old, from session-01 incoming
├── DECISIONS.md              # Exists but not updated
├── PROGRESS.md               # Exists but not updated
├── incoming/
│   ├── session-01/           # Has old project-wide docs mixed in
│   ├── session-02/
│   └── session-03/
└── outgoing/
    ├── session-01/           # Has ARCHITECTURE_OVERVIEW.md etc.
    └── session-02/
```

**Target (clean):**
```
docs/
├── DECISIONS.md              # Project-wide, updated with all decisions
├── PROGRESS.md               # Project-wide, updated with session summaries
├── ARCHITECTURE.md           # Project-wide system design (consolidated)
├── incoming/                 # Session-specific input docs only
│   ├── session-01/
│   ├── session-02/
│   └── session-03/
└── outgoing/                 # Session-specific output docs only
    ├── session-01/
    └── session-02/
```

**After Part A is complete: STOP and commit with message "Reorganize documentation structure"**

### Part B: Play vs Coach Mode

Build the ability to play against Stockfish at adjustable difficulty levels.

---

## Technical Decisions (Pre-Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Difficulty control | UCI_LimitStrength + UCI_Elo | Built into Stockfish, no custom logic needed |
| ELO range | 800 - 2800 | Covers beginner to master level |
| Default ELO | 1200 | Reasonable starting point for casual players |
| Game state | Frontend manages | Simple for MVP, backend stays stateless |
| Move response | New endpoint `/api/move` | Cleaner than overloading `/api/analyze` |

---

## Stockfish ELO Limiting

Stockfish supports skill limiting via UCI options:

```python
await engine.configure({
    "UCI_LimitStrength": True,
    "UCI_Elo": 1200  # Range: 800-2800 for Stockfish
})
```

When `UCI_LimitStrength` is True, Stockfish plays at approximately the specified ELO level by:
- Limiting search depth
- Occasionally making suboptimal moves
- Simulating human-like play patterns

---

## Session 02 Decisions to Log

These need to be added to DECISIONS.md during Part A:

```markdown
### [DECISION-005] FastAPI for Backend Framework
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Needed to choose between Flask and FastAPI for the Python backend.
**Decision:** Use FastAPI
**Rationale:** 
- Native async support (important for Stockfish subprocess)
- Auto-generated OpenAPI docs at /docs
- Modern Python patterns (type hints, Pydantic)
- Better scaling for future concurrent requests
**Consequences:** 
- Requires uvicorn as ASGI server
- Slightly steeper learning curve than Flask

### [DECISION-006] Evaluation from White's Perspective
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Stockfish can report evaluation from side-to-move perspective (.relative) or White's perspective (.white()).
**Decision:** Always report from White's perspective
**Rationale:**
- Matches industry standard (Chess.com, Lichess, all major platforms)
- Positive = White better, Negative = Black better (intuitive)
- Consistent regardless of whose turn it is
**Consequences:**
- Frontend doesn't need to flip sign based on turn
- Easier to understand evaluation trends across a game

### [DECISION-007] Keep Engine Alive Between Requests
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Could create new Stockfish process per request or keep one alive.
**Decision:** Keep engine alive using FastAPI lifespan
**Rationale:**
- Faster response times (no startup overhead)
- Lower resource churn
- Stockfish designed for persistent use
**Consequences:**
- Single engine instance handles all requests sequentially
- Need to manage engine lifecycle carefully
- May need multiple instances for concurrent users (future)

### [DECISION-008] Default Analysis Depth of 15
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Higher depth = better analysis but slower.
**Decision:** Default to depth 15, allow override via API
**Rationale:**
- ~1-2 second response time
- Good accuracy for coaching purposes
- Depth 20+ takes 5-10+ seconds
**Consequences:**
- May miss very deep tactics
- Can increase for "deep analysis" mode later
```

---

## Commands Reference

```bash
# Navigate to project
cd ~/myCodes/projects/chess-coach

# Activate venv
source venv/bin/activate

# Run backend
cd src/backend
uvicorn main:app --reload --port 8000

# Test new move endpoint (after Part B)
curl -X POST http://localhost:8000/api/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "elo": 1200}'
```

---

## Reference Files

- `docs/outgoing/session-02/SESSION_SUMMARY.md` — What was built in Session 02
- `docs/outgoing/session-01/ARCHITECTURE_OVERVIEW.md` — System design (to consolidate)
- `docs/outgoing/session-01/STOCKFISH_INTEGRATION_GUIDE.md` — Stockfish technical details
