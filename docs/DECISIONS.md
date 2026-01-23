# Architecture Decisions Log

This document tracks key technical and design decisions with rationale. When Claude Code or future-you wonders "why did we do it this way?", the answer should be here.

---

## Decision Format

```
### [DECISION-XXX] Short Title
**Date:** YYYY-MM-DD
**Status:** Accepted / Superseded / Deprecated
**Context:** What situation prompted this decision?
**Decision:** What did we choose?
**Rationale:** Why this over alternatives?
**Consequences:** What does this enable or constrain?
```

---

## Decisions

### [DECISION-001] Use WSL as Development Environment
**Date:** 2025-01-22
**Status:** Accepted
**Context:** Need to choose between native Windows, WSL, or dual setup for development.
**Decision:** All development happens in WSL (Ubuntu).
**Rationale:**
- TensorFlow and ML libraries work better on Linux
- Stockfish and Python chess libraries are Linux-native
- Avoids path/subprocess issues mixing Windows binaries with WSL Python
- Better ecosystem consistency
**Consequences:**
- All paths are Linux paths
- VS Code must connect via WSL extension
- Files stored in WSL filesystem, not Windows

---

### [DECISION-002] Stockfish via System Package
**Date:** 2025-01-22
**Status:** Accepted
**Context:** Stockfish can be installed via apt, compiled from source, or downloaded as binary.
**Decision:** Install via `sudo apt install stockfish`
**Rationale:**
- Simplest installation
- Automatically in PATH for python-chess to find
- Easy to update via apt
- Good enough for development; can optimize later if needed
**Consequences:**
- May not be the absolute latest Stockfish version
- Limited control over compilation flags
- If we need bleeding-edge, will need to revisit

---

### [DECISION-003] chessboard.js + chess.js for Frontend
**Date:** 2025-01-22
**Status:** Accepted
**Context:** Need an interactive chessboard UI. Options: build from scratch, chessboard.js, lichess board, react-chessboard.
**Decision:** Use chessboard.js for rendering + chess.js for logic
**Rationale:**
- Mature, well-documented libraries
- Separation of concerns (board display vs game logic)
- No framework dependency initially
- Can be controlled programmatically (key for AI integration)
- Don't reinvent the wheel—focus energy on the AI coaching layer
**Consequences:**
- Vanilla JS initially (fine for MVP)
- May migrate to react-chessboard if we adopt React later
- Need to manage two libraries' coordination

---

### [DECISION-004] PGN Files Inside Project Repo
**Date:** 2025-01-22
**Status:** Accepted
**Context:** Where to store sample PGN files for development and testing?
**Decision:** Store in `data/samples/` within the project
**Rationale:**
- Claude Code can access them directly
- Consistent test fixtures for development
- Easy relative paths in code
- Can gitignore personal games if needed
**Consequences:**
- Need to be mindful of repo size if many PGNs accumulate
- Personal games in repo (mitigated by gitignore option)

---

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

---

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

---

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

---

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

---

*Add new decisions as they're made. Don't delete old ones—mark as superseded if changed.*
