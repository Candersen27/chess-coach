# Session 04.5 Tasks - PROJECT_WALKTHROUGH.md Creation

---

## Pre-Task: Read the Codebase

Before writing, read and understand:

- [ ] `src/frontend/chessboard.html` - All JavaScript functions, how they connect
- [ ] `src/backend/main.py` - FastAPI app, endpoints, request/response flow
- [ ] `src/backend/engine.py` - Stockfish wrapper, async patterns
- [ ] `docs/DECISIONS.md` - All 12 decisions and their rationale
- [ ] `docs/PROGRESS.md` - Session summaries
- [ ] `docs/outgoing/session-*/SESSION_SUMMARY.md` - Detailed session reports

---

## Task 1: Create PROJECT_WALKTHROUGH.md

Create the file at project root: `PROJECT_WALKTHROUGH.md`

### Required Sections

#### 1. Opening Hook
- What is this project? (2-3 sentences, compelling)
- What problem does it solve?
- What makes it interesting?

#### 2. The Big Picture
- High-level architecture (explain like you're drawing on a whiteboard)
- How the pieces fit together
- Use a simple analogy for the whole system

#### 3. The Frontend Story
- What chessboard.js and chess.js do (and why we use both)
- How the board is "AI-controllable" (the key insight)
- The three modes: navigation, analysis, play
- How state is managed (game history, current position, play mode flags)

#### 4. The Backend Story
- Why FastAPI (not Flask)
- The Stockfish conversation (subprocess, UCI protocol - use the "notes under door" analogy or similar)
- Async patterns and why they matter
- How the engine stays alive between requests (lifespan management)

#### 5. How Analysis Works
- Single position: FEN → Stockfish → evaluation + best move
- Full game: iterate through moves, classify each one
- The evaluation perspective convention (always from White's view)
- Move classification thresholds and why they exist
- Accuracy calculation (the simplified formula and why it's good enough)

#### 6. How Play Mode Works
- The ELO limiting trick (UCI_LimitStrength + UCI_Elo)
- Turn management in the frontend
- The request/response cycle when you make a move
- Why the backend is stateless (frontend manages game state)

#### 7. The Data Flow
- Trace a complete user action through the system:
  - "User loads PGN → clicks Analyze → sees results"
  - "User makes move in play mode → coach responds"
- Show how frontend and backend communicate

#### 8. Technical Decisions Explained
- Don't just list decisions - explain the *thinking*
- Group related decisions together
- Include "what we considered" and "why we chose this"

Key decisions to explain:
- WSL as development environment
- FastAPI over Flask
- Keeping Stockfish alive vs. spawning per request
- Evaluation from White's perspective
- Frontend managing game state
- Classification thresholds
- Simplified accuracy formula

#### 9. Bugs We Hit and What They Taught Us

For each bug, structure as:
- What went wrong
- How we discovered it
- The root cause
- The fix
- The lesson (what to watch for in future projects)

Bugs to cover:
1. Piece images not rendering
2. python-chess async API mismatch
3. Evaluation perspective confusion
4. Stockfish minimum ELO surprise
5. 100% accuracy for both players bug
6. Unresponsive analyze button
7. Invisible/tiny chessboard

#### 10. Patterns Worth Reusing

Extract generalizable patterns:
- Async engine management in Python
- Frontend state management without a framework
- API design for chess applications
- Error handling patterns
- The "two-part session" approach (cleanup + feature)

#### 11. What Good Engineering Looks Like

Observations about the development process:
- Starting with the data layer before the AI layer
- Documentation-driven development (incoming/outgoing docs)
- Making decisions explicit and logged
- Building the simplest thing that works, then iterating
- The value of a backlog for polish items

#### 12. Where This Is Going

Brief preview of Phase 2+:
- Database for player profiles (persistent memory)
- Claude API for natural language coaching
- RAG for chess literature references
- How Phase 1 sets up these future capabilities

#### 13. Quick Reference

At the end, a concise reference section:
- How to run the project (copy from README)
- Key files and what they do
- API endpoints (brief)

---

## Task 2: Quality Check

After writing, verify:

- [ ] Someone unfamiliar with the project could understand it
- [ ] Technical accuracy (code references are correct)
- [ ] Engaging tone throughout (not dry)
- [ ] Analogies are clear and helpful
- [ ] Bugs section is honest and educational
- [ ] No redundancy with README.md (walkthrough goes deeper, README is quickstart)

---

## Task 3: Update Other Docs

- [ ] Add entry to `docs/PROGRESS.md` for Session 04.5
- [ ] Add to root README.md: link to PROJECT_WALKTHROUGH.md with description
  ```markdown
  ## Documentation
  
  - **[PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md)** - Deep dive into how everything works, 
    why we made the decisions we did, and lessons learned
  ```

---

## Deliverables Checklist

- [ ] `PROJECT_WALKTHROUGH.md` created at project root
- [ ] All 13 sections completed
- [ ] Engaging, narrative tone throughout
- [ ] Bugs and lessons included
- [ ] Code examples where helpful
- [ ] `docs/PROGRESS.md` updated
- [ ] Root `README.md` updated with link
- [ ] Git committed and pushed

---

## File Location

```
chess-coach/
├── README.md                    # Quick start (exists)
├── PROJECT_WALKTHROUGH.md       # NEW - the deep understanding doc
├── docs/
└── src/
```

---

## Notes for Claude Code

- **Read the actual code**, not just the docs. The walkthrough should reflect what's really there.
- **Use specific code snippets** where they illuminate a point, but don't dump entire files.
- **The tone is crucial.** If a section sounds like a textbook, rewrite it.
- **Analogies help.** The "notes under door" example in CONTEXT.md is the kind of thing we want.
- **Be honest about bugs.** They're learning opportunities, not embarrassments.
- **This is a portfolio piece.** It should demonstrate understanding and communication skills.
