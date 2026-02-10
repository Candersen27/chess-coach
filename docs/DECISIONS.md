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

### [DECISION-009] ELO Range 1350-2800 for Play Mode
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Stockfish UCI_Elo has minimum value determined by version/build.
**Decision:** Support ELO range 1350-2800 (based on installed Stockfish version)
**Rationale:**
- Installed Stockfish minimum UCI_Elo is 1350, not 800 as originally planned
- 1350-2800 still covers intermediate to grandmaster level
- Use Stockfish's built-in UCI_LimitStrength feature
**Consequences:**
- No beginner level below 1350
- May need alternative weakening strategy for true beginners (future)
- Frontend UI adjusted to reflect actual range

---

### [DECISION-010] Frontend Manages Game State (Stateless Backend)
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Need to decide where game state lives for play-vs-coach mode.
**Decision:** Frontend manages all game state; backend remains stateless
**Rationale:**
- Simpler backend architecture
- No session management needed
- Frontend already has chess.js for move validation
- Easier to scale backend (no state to sync)
- Fits well with current architecture
**Consequences:**
- Frontend tracks: current position, move history, whose turn, player color
- Backend only provides: analysis, engine moves (stateless requests)
- Cannot resume games after page refresh (acceptable for MVP)
- May add database persistence later for game history

---

### [DECISION-011] Move Classification Thresholds
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Need standardized thresholds for classifying move quality based on centipawn loss.
**Decision:** Use thresholds: Excellent (≤0 CP), Good (0-20 CP), Inaccuracy (20-50 CP), Mistake (50-100 CP), Blunder (>100 CP)
**Rationale:**
- Matches Chess.com and Lichess standards
- Well-understood by chess players
- Based on practical impact of centipawn losses
- Provides granular feedback for different skill levels
**Consequences:**
- Consistent move classification across all games
- Easy to compare analysis with other platforms
- May be harsh for beginners (100+ CP losses are common)
- Could adjust thresholds per skill level in future

---

### [DECISION-012] Simplified Accuracy Formula
**Date:** 2025-01-23
**Status:** Accepted
**Context:** Need formula to convert average centipawn loss to accuracy percentage.
**Decision:** Use simplified formula: `accuracy = max(0, min(100, 100 - (avg_cp_loss / 2)))`
**Rationale:**
- Simple linear relationship, easy to understand
- Good enough for MVP - provides meaningful feedback
- More complex Chess.com formula (`103.1668 * exp(-0.04354 * avg_loss) - 3.1668`) can be added later
- Linear formula is more predictable for users
**Consequences:**
- Accuracy percentages will differ from Chess.com
- May show higher accuracy for mediocre play than exponential formula
- Easy to refine formula later without changing analysis infrastructure
- Users can still compare relative performance across their own games

---

### [DECISION-013] Claude Sonnet for Chat Model
**Date:** 2025-01-30
**Status:** Accepted
**Context:** Need to choose Claude model for coaching chat. Options: Haiku (fast/cheap), Sonnet (balanced), Opus (highest quality).
**Decision:** Use claude-sonnet-4-20250514
**Rationale:**
- Good balance of quality and cost for conversational coaching
- Fast enough for chat-style interactions
- Smart enough for chess concept explanations
- Can upgrade to Opus for specific deep analysis later if needed
**Consequences:**
- ~$3/MTok input, ~$15/MTok output
- Responses typically under 2 seconds
- Quality sufficient for teaching concepts (not engine-level calculation)

---

### [DECISION-014] Conversation State in Frontend
**Date:** 2025-01-30
**Status:** Accepted
**Context:** Conversation history needs to persist across messages. Options: frontend array, backend sessions, database.
**Decision:** Frontend manages conversation history as a JavaScript array, sent with each request
**Rationale:**
- Simplest implementation for MVP
- No backend session management needed
- Consistent with DECISION-010 (frontend manages game state)
- Stateless backend remains easy to scale
- Full history sent each request means Claude has complete context
**Consequences:**
- Conversation lost on page refresh (acceptable for MVP)
- Token usage grows with conversation length (mitigated by max_tokens)
- Will add database persistence in Phase 3
- No server-side conversation logging (privacy benefit for MVP)

---

### [DECISION-015] AsyncAnthropic Client
**Date:** 2025-01-30
**Status:** Accepted
**Context:** Anthropic SDK provides both sync (Anthropic) and async (AsyncAnthropic) clients.
**Decision:** Use AsyncAnthropic to match the project's async-first backend pattern
**Rationale:**
- Consistent with engine.py async patterns
- Doesn't block the FastAPI event loop during API calls
- Allows concurrent request handling if needed later
**Consequences:**
- Coach chat method is properly async
- Consistent architecture across all backend modules

---

### [DECISION-016] Full Context + Prompt Caching Over RAG
**Date:** 2025-02-10
**Status:** Accepted
**Context:** Need to integrate chess book content (~65K tokens) into coaching conversations. Options: RAG with vector embeddings, keyword search, or full context inclusion.
**Decision:** Include full book content in system prompt with Anthropic's prompt caching.
**Rationale:**
- For 1-3 books (~200K tokens), full context is simpler and more accurate than vector search
- No retrieval errors — Claude sees the entire book
- Prompt caching reduces cost by ~90% on the cached portion after the first call
- Avoids complexity of embedding pipeline, vector database, chunk management
- Scaling path documented: keyword search at 4-10 books, embeddings at 10+
**Consequences:**
- First API call in a session pays full price for ~65K tokens
- Subsequent calls benefit from prompt caching (~90% discount)
- System prompt is large but Claude handles it well
- Cannot exceed context window limit (currently 200K tokens)

---

### [DECISION-017] Lesson Plan JSON Structure with [LESSON_PLAN] Marker
**Date:** 2025-02-10
**Status:** Accepted
**Context:** Need structured lesson plans from coaching conversations. Options: separate API call, tool use, inline JSON.
**Decision:** Claude includes lesson plan JSON at end of message after `[LESSON_PLAN]` marker.
**Rationale:**
- Keeps conversational response and structured data in a single API call
- Easy to parse — split on marker, extract JSON
- Claude's response reads naturally without the JSON clutter
- Frontend receives both the chat message and the plan in one response
- No extra API round-trip needed
**Consequences:**
- Must handle parsing failures gracefully (JSON might be malformed)
- Lesson plan only generated when student explicitly agrees to practice
- `suggested_action` field in ChatResponse carries the plan to frontend
- Lesson plans are generated but not executed yet (Session 07)

---

*Add new decisions as they're made. Don't delete old ones—mark as superseded if changed.*
