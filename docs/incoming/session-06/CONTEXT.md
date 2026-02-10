# Session 06 Context - Lesson Plan Generation + Book Integration

> **Date:** January 26, 2025
> **Phase:** Phase 2 - AI Coaching Layer
> **Session Goal:** Structure chess book, integrate into coaching context, enable lesson plan generation

---

## Phase 2 Progress

| Session | Focus | Status |
|---------|-------|--------|
| 05 | Claude API + Chat Interface | ✅ Complete |
| **06** | **Lesson Plan Generation + Book Integration** | **This Session** |
| 07 | Board Integration (Claude controls coached play) | Next |

---

## What Exists (Session 05 Complete)

### Backend
- `src/backend/coach.py` — Claude API wrapper with coaching persona
- `src/backend/main.py` — Includes `POST /api/chat` endpoint
- Chat accepts conversation history + board context

### Frontend
- Chat panel alongside chessboard
- Conversation history managed in JavaScript
- Board context passed with each message

### New Resource
- `data/books/chess_fundamentals_capablanca.txt` — Full text of Capablanca's Chess Fundamentals (6,512 lines, ~65K tokens)

---

## What We're Building This Session

### 1. Book Parsing & Structuring

Convert raw text into structured JSON for flexible use:

```json
{
  "title": "Chess Fundamentals",
  "author": "José Raúl Capablanca",
  "year": 1921,
  "parts": [
    {
      "part_number": 1,
      "title": "First Principles: Endings, Middle-game and Openings",
      "chapters": [
        {
          "chapter_number": 1,
          "title": "First Principles",
          "sections": [
            {
              "section_number": 1,
              "title": "Some Simple Mates",
              "topics": ["rook mate", "two bishops mate", "queen mate"],
              "content": "The first thing a student should do..."
            }
          ]
        }
      ]
    }
  ],
  "illustrative_games": [
    {
      "game_number": 1,
      "white": "F. J. Marshall",
      "black": "J. R. Capablanca",
      "opening": "Queen's Gambit Declined",
      "event": "Match, 1909",
      "content": "..."
    }
  ]
}
```

### 2. Book Integration (Prompt Caching Approach)

**Why not RAG:** For 1-3 books (~200K tokens), full context with prompt caching is simpler and more accurate than vector search. No retrieval errors.

**Implementation:**
- Load structured book on coach initialization
- Include full book (or relevant parts) in system prompt
- Use Anthropic's prompt caching to reduce cost on subsequent calls

**Scaling path (documented, not built):**
- Level 1 (now): Full context + caching
- Level 2 (4-10 books): Keyword/topic search over sections
- Level 3 (10+ books): Add embeddings for semantic search

### 3. Lesson Plan Generation

When conversation reaches a natural "let's practice" moment, Claude generates a structured lesson plan:

```json
{
  "id": "lesson_20250126_001",
  "topic": "Basic Rook Endgames",
  "type": "endgame_practice",
  "source_reference": {
    "book": "Chess Fundamentals",
    "chapter": "Further Principles in End-Game Play",
    "section": "A Classical Ending"
  },
  "goals": [
    "Understand the Lucena position",
    "Practice building the bridge",
    "Recognize when to activate the rook"
  ],
  "activity": {
    "type": "position_study",
    "positions": [
      {
        "fen": "1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1",
        "instruction": "This is the Lucena position. White to play and win.",
        "goal": "Build the bridge to promote the pawn"
      }
    ]
  },
  "teaching_notes": [
    "If student struggles, show the rook lift (Rc4-Rc8)",
    "Emphasize king shelter concept",
    "Reference Capablanca's explanation on page 37"
  ],
  "success_criteria": "Student can execute the bridge technique without hints"
}
```

### 4. Activity Types

| Type | Description | Board Behavior |
|------|-------------|----------------|
| `practice_game` | Play a full game with coaching goals | Coach plays, selects moves based on lesson |
| `position_study` | Walk through specific positions | Board shows positions, coach explains |
| `tactics_drill` | Find the best move challenges | Board shows puzzle, waits for user move |
| `endgame_practice` | Guided endgame technique | Similar to position study, more interactive |
| `game_review` | Analyze a real game | Load PGN, step through with commentary |

### 5. Conversation → Activity Flow

```
User: "I keep losing rook endgames"
    ↓
Coach: "Rook endgames are tricky! Capablanca dedicated a whole 
        chapter to them. What specifically gives you trouble - 
        converting a pawn advantage, or defending difficult positions?"
    ↓
User: "Converting when I have an extra pawn"
    ↓
Coach: "That's the Lucena position - the most important pattern to know.
        Want me to show you how it works?"
    ↓
User: "Yes please"
    ↓
Coach: [generates lesson plan internally]
Coach: "Let's do it. I'll set up the classic Lucena position.
        Your goal is to promote the pawn using a technique called
        'building the bridge.' Ready?"
    ↓
[Activity launches with lesson plan context]
```

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Book storage | Structured JSON | Enables future keyword search without re-parsing |
| Context approach | Full book + prompt caching | Simpler than RAG, no retrieval errors, scales to 3 books |
| Lesson plan storage | In-memory for now | Database comes in Phase 3 |
| Activity trigger | Explicit user confirmation | "Want to practice?" → "Yes" → activity starts |

---

## Book Structure Details

Chess Fundamentals has clear markers we can parse:

**Part markers:** `PART I`, `PART II`

**Chapter markers:** `CHAPTER I`, `CHAPTER II`, etc.

**Section markers:** Numbered sections like `1. SOME SIMPLE MATES`, `2. PAWN PROMOTION`

**Game markers:** `GAME.` followed by number and details

**Notation:** Uses descriptive notation (K-B6) not algebraic (Kf6). Claude understands both.

---

## Prompt Caching Implementation

Anthropic's prompt caching caches the static prefix of prompts:

```python
# First call: Full price for book content
# Subsequent calls: 90% discount on cached portion

system_prompt = f"""You are a chess coach...

Reference Material:
{book_content}  # This part gets cached

Current conversation context:
"""  # This part is new each time
```

The book content (~65K tokens) only costs full price once per session.

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/parse_book.py` | Create | Parse raw text → structured JSON |
| `data/books/chess_fundamentals.json` | Create | Structured book data |
| `src/backend/books.py` | Create | Book loading and search utilities |
| `src/backend/lesson.py` | Create | Lesson plan generation and management |
| `src/backend/coach.py` | Modify | Integrate book content, lesson plan generation |
| `src/backend/main.py` | Modify | Add lesson plan endpoints if needed |

---

## API Changes

### Modified: POST /api/chat

Response now may include a lesson plan:

```json
{
  "message": "Let's practice the Lucena position...",
  "suggested_action": {
    "type": "start_lesson",
    "lesson_plan": { ... }
  }
}
```

### New: GET /api/books (optional)

List available books and their topics (for future UI).

### New: POST /api/lesson/start (optional)

Explicitly start a lesson from a plan.

---

## Success Criteria

1. Book parsed into structured JSON with chapters/sections
2. Coach references book content naturally in conversation
3. Lesson plan generated when user agrees to practice
4. Lesson plan includes specific positions, goals, teaching notes
5. Activity type determined by lesson topic
6. Source references point to actual book sections

---

## Out of Scope (Session 07)

- Claude actually controlling the board based on lesson plan
- Multi-PV move selection during coached play
- Real-time commentary during activities

---

## Commands Reference

```bash
# Parse the book
cd ~/myCodes/projects/chess-coach
source venv/bin/activate
python scripts/parse_book.py

# Verify JSON created
cat data/books/chess_fundamentals.json | head -100

# Run backend
cd src/backend
uvicorn main:app --reload --port 8000

# Test chat with book reference
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I win a rook endgame with an extra pawn?",
    "conversation_history": [],
    "board_context": null
  }'
```

---

## Reference Files

- `data/books/chess_fundamentals_capablanca.txt` — Raw book text
- `src/backend/coach.py` — Current coach implementation
- `docs/PROJECT_WALKTHROUGH.md` — System overview
