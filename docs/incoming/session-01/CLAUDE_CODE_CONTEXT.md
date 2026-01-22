# Claude Code Context - Chess Coach Project

> **Last Updated:** January 22, 2025
> **Current Phase:** Phase 1 - Technical Foundation
> **Session Goal:** Build interactive chessboard with PGN support

---

## Project Summary

An AI-powered personalized chess coach that analyzes games, learns player-specific patterns and weaknesses, and provides tailored training. The core differentiator: the coach *remembers* and builds a persistent understanding of each player over time.

**Key Concept:** The AI controls the chessboard as a "shared whiteboard" for coaching conversations—setting up positions, stepping through games, creating custom training scenarios.

---

## Current State

### What Exists
- Project folder structure in WSL: `~/projects/chess-coach/`
- Stockfish installed via apt (`stockfish` command available)
- Sample PGN file: `data/samples/` (user's own game from Chess.com)

### What We're Building This Session
1. **Interactive chessboard webpage** using chessboard.js + chess.js
2. **PGN import functionality** - load a file and step through moves
3. **Basic Python backend** that can serve the page and will later integrate with Stockfish

---

## Technical Decisions (Already Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Environment | WSL (Ubuntu) | TensorFlow compatibility, consistent Linux ecosystem |
| Language | Python | Creator proficiency, good chess/ML libraries |
| Chess Engine | Stockfish | Open source, strongest engine, no API costs |
| Chess UI | chessboard.js | Don't reinvent the wheel, focus on AI integration |
| LLM | Claude API | For coaching conversation (future phase) |
| Database | PostgreSQL with JSONB | Flexible schema for game analysis data (future phase) |

---

## Folder Structure

```
chess-coach/
├── data/
│   └── samples/           # Test PGN files
├── docs/
│   ├── CLAUDE_CODE_CONTEXT.md   # This file
│   ├── DECISIONS.md             # Architecture decisions log
│   └── PROGRESS.md              # Session-by-session progress
├── src/
│   ├── backend/           # Python API (Flask or FastAPI)
│   │   └── ...
│   └── frontend/          # Web UI
│       └── ...
├── tests/
├── requirements.txt
└── README.md
```

---

## Immediate Task: Interactive Chessboard

### Requirements
1. HTML page with a chessboard (using chessboard.js)
2. Chess move validation (using chess.js)
3. Load PGN button/input
4. Forward/back buttons to step through game moves
5. Display current move notation and move number
6. Board should be controllable programmatically (for future AI control)

### Implementation Notes
- Use CDN links for chessboard.js and chess.js initially (simplicity)
- Can be a simple static HTML file to start—Python backend integration comes after
- The board must expose JavaScript functions that can be called to:
  - Set any arbitrary position (FEN string)
  - Make a move
  - Reset to starting position
  - Load a full PGN

### Libraries
- **chessboard.js:** https://chessboardjs.com/ (board rendering, drag-drop)
- **chess.js:** https://github.com/jhlywa/chess.js (move validation, PGN parsing)

---

## Future Context (Not for This Session)

These features come later—listed here so architectural choices don't paint us into a corner:

- **Stockfish integration:** Python subprocess, analyze positions, return evaluations
- **Claude API integration:** Coaching conversation based on analysis
- **User profiles:** PostgreSQL database storing games, patterns, preferences
- **Lichess/Chess.com API:** Fetch user games instead of manual PGN upload
- **RAG knowledge base:** Chess literature for contextual coaching

---

## Commands Reference

```bash
# Verify Stockfish works
stockfish

# Start Python virtual environment (create if needed)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt
```

---

## Questions to Resolve This Session

1. Flask vs FastAPI for the backend? (Leaning FastAPI for async + modern patterns)
2. Serve frontend from Python backend or separate static server for dev?

---

## Creator Context

- BS Statistics, CS minor, MS Data Science (in progress)
- Python proficient, learning web dev
- Competitive gaming background (MTG, Disney Lorcana top 50)
- Learns best by building, not courses
- This is a personal tool first—if it helps the creator improve at chess, it's validated

---

*Hand this file to Claude Code at the start of each session. Update "Current State" and "Session Goal" as you progress.*
