# Session 05 Context - Claude API + Minimal Chat Interface

> **Date:** January 26, 2025
> **Phase:** Phase 2 - AI Coaching Layer
> **Session Goal:** Integrate Claude API with minimal chat UI alongside the chessboard

---

## Phase 2 Overview

Phase 1 built the chess foundation (board, Stockfish analysis, play mode). Phase 2 adds the AI coaching layer.

**Phase 2 sessions:**
- **Session 05 (this one):** Claude API + minimal chat interface
- **Session 06:** Lesson plan generation from conversation
- **Session 07:** Board integration (Claude controls coached play via lesson plan)

---

## What Exists (Phase 1 Complete)

### Backend (`src/backend/`)
- `main.py` — FastAPI with endpoints: health, analyze, move, game/analyze
- `engine.py` — Async Stockfish wrapper
- Virtual environment with python-chess, fastapi, uvicorn

### Frontend (`src/frontend/chessboard.html`)
- Interactive chessboard (chessboard.js + chess.js)
- PGN loading and navigation
- Single position and full game analysis
- Play vs Coach mode
- PGN export

### New This Session
- `.env` file at project root with `ANTHROPIC_API_KEY`
- User has obtained API key from console.anthropic.com

---

## What We're Building This Session

### 1. Backend: Chat Endpoint

New endpoint for conversing with the coach:

```
POST /api/chat
```

**Request:**
```json
{
  "message": "I keep losing to the London System. Can you help?",
  "conversation_history": [
    {"role": "user", "content": "Hi, I want to improve at chess"},
    {"role": "assistant", "content": "I'd love to help! What aspect..."}
  ],
  "board_context": {
    "fen": "current position if relevant",
    "last_move": "e4",
    "mode": "analysis" | "play" | "idle"
  }
}
```

**Response:**
```json
{
  "message": "The London System can be frustrating! Let's look at...",
  "suggested_action": null | {
    "type": "set_position" | "start_game" | "load_pgn",
    "data": {...}
  }
}
```

The `suggested_action` field allows Claude to propose board actions (not used yet, but architecture supports it for Session 07).

### 2. Backend: Claude Integration

Create `src/backend/coach.py`:
- Load API key from environment
- Define coaching system prompt
- Handle conversation with Claude API
- Manage context (board state, conversation history)

### 3. Frontend: Minimal Chat UI

Add to `chessboard.html`:
- Chat panel (right side or below board)
- Message input field
- Send button
- Message display area (scrollable)
- Basic styling (functional, not polished)

Layout:
```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │                     │  │  Coach: Hi! I'm your chess   │  │
│  │     CHESSBOARD      │  │  coach. What would you like  │  │
│  │                     │  │  to work on today?           │  │
│  │                     │  │                              │  │
│  │                     │  │  You: I struggle with        │  │
│  │                     │  │  endgames                    │  │
│  │                     │  │                              │  │
│  │                     │  │  Coach: Endgames are crucial │  │
│  │                     │  │  ...                         │  │
│  └─────────────────────┘  │                              │  │
│  [Analysis] [Play] [etc]  │  ┌────────────────────┐ [Send]│  │
│                           │  │ Type message...    │      │  │
│                           │  └────────────────────┘      │  │
│                           └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## The Coaching Persona

Claude should act as a friendly, knowledgeable chess coach. Key traits:

- **Patient and encouraging** — Chess improvement takes time
- **Socratic** — Asks questions to understand what user needs
- **Concrete** — Uses specific positions and examples, not just abstract advice
- **Honest about limitations** — Doesn't pretend to calculate like an engine
- **Aware of the board** — Can reference current position when relevant

### System Prompt (Draft)

```
You are a friendly chess coach helping a student improve their game.

Your approach:
- Ask questions to understand what the student wants to work on
- Give concrete, actionable advice (not vague platitudes)
- Use the chessboard to illustrate points when helpful
- Be encouraging but honest about mistakes
- Reference established chess principles and, when available, chess literature

You have access to a chessboard that can display positions. When it would help your explanation, you can suggest setting up a specific position.

You do NOT calculate tactics yourself — that's what the chess engine is for. Your job is to explain concepts, guide learning, and help the student understand WHY moves are good or bad.

Current board state: {board_context}
```

---

## Technical Decisions (Pre-Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API key storage | `.env` file + python-dotenv | Secure, standard practice |
| Conversation state | Frontend manages | Simple for MVP, no backend sessions needed |
| Chat UI | Same page as board | User sees both simultaneously |
| Claude model | claude-sonnet-4-20250514 | Good balance of quality and cost for chat |
| Streaming | Not for MVP | Simpler without, add later if latency is an issue |

---

## Dependencies to Add

```bash
pip install anthropic python-dotenv
```

Update `requirements.txt`:
```
fastapi
uvicorn[standard]
python-chess
anthropic
python-dotenv
```

---

## Environment Setup

`.env` file at project root:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

`.gitignore` must include:
```
.env
```

---

## Not In Scope (Future Sessions)

- Document upload (later polish session)
- Lesson plan generation (Session 06)
- Claude controlling the board (Session 07)
- RAG with chess books (Session 06 or 07)
- Persistent conversation history (Phase 3 with database)
- Sophisticated chat UI styling (later polish session)

---

## Commands Reference

```bash
# Navigate to project
cd ~/myCodes/projects/chess-coach

# Activate venv
source venv/bin/activate

# Install new dependencies
pip install anthropic python-dotenv
pip freeze > src/backend/requirements.txt

# Run backend
cd src/backend
uvicorn main:app --reload --port 8000

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, I want to get better at chess",
    "conversation_history": [],
    "board_context": null
  }'
```

---

## Success Criteria

1. Backend loads API key from `.env`
2. `POST /api/chat` returns Claude's response
3. Frontend displays conversation
4. User can have multi-turn conversation
5. Board context is passed to Claude (even if not used yet)
6. Conversation feels natural and coach-like

---

## Reference Files

- `docs/PROJECT_WALKTHROUGH.md` — How the system works
- `docs/ARCHITECTURE.md` — System overview
- `src/backend/main.py` — Existing FastAPI app to extend
- `src/frontend/chessboard.html` — Existing frontend to extend
