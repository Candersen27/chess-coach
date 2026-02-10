# Session 06 Summary - Lesson Plan Generation + Book Integration

> **Date:** February 10, 2025
> **Phase:** Phase 2 - AI Coaching Layer
> **Outcome:** Success

---

## What Was Built

### Book Parser (`scripts/parse_book.py`)
- Parses Capablanca's "Chess Fundamentals" from raw Project Gutenberg text
- Strips Gutenberg header/footer, title pages, and table of contents
- Extracts 33 sections across 6 chapters (Part I) and 14 illustrative games (Part II)
- Generates topic keywords per section for future search capability
- Outputs structured JSON to `data/books/chess_fundamentals.json`

### Book Integration Module (`src/backend/books.py`)
- `BookLibrary` class loads all JSON books from `data/books/`
- `get_section()` — retrieve specific section by number
- `search_topics()` — keyword search across all sections
- `format_for_prompt()` — format entire book for Claude's system prompt
- Auto-discovers and loads new books added as JSON files

### Lesson Plan Module (`src/backend/lesson.py`)
- Pydantic models: `LessonPlan`, `LessonActivity`, `Position`, `SourceReference`
- Activity types: `practice_game`, `position_study`, `tactics_drill`, `endgame_practice`, `game_review`
- `LessonManager` — tracks current lesson and history
- `extract_lesson_json()` — parses lesson plan from Claude's response

### Updated Coach (`src/backend/coach.py`)
- Book content included in system prompt with prompt caching
- System prompt instructs Claude to reference Capablanca and generate lesson plans
- Response parsing extracts `[LESSON_PLAN]` marker and JSON
- Returns `suggested_action` with lesson plan when generated

### Updated API (`src/backend/main.py`)
- `GET /api/books` — list available books with chapters and topics
- `POST /api/chat` — now returns `suggested_action.lesson_plan` when applicable

### Updated Frontend (`src/frontend/chessboard.html`)
- Lesson plan card display in chat (topic, type, goals, source reference)
- Lesson active banner at top of chat panel
- `currentLessonPlan` stored for Session 07 board integration

---

## Architecture After Session 06

```
Frontend (chessboard.html)
├── Chessboard (chessboard.js + chess.js)
├── Analysis/Play/Game panels
└── Chat panel ──→ POST /api/chat ──→ coach.py ──→ Claude API
    │                                    ├── BookLibrary (book content in system prompt)
    │                                    └── LessonManager (lesson plan extraction)
    └── Lesson plan card display ←── suggested_action.lesson_plan

Backend (FastAPI)
├── main.py (routes: health, analyze, move, game/analyze, chat, books)
├── engine.py (Stockfish wrapper)
├── coach.py (Claude API + book integration + lesson plans) ← MODIFIED
├── books.py (Book library module) ← NEW
└── lesson.py (Lesson plan models and management) ← NEW

Data
├── data/books/chess_fundamentals_capablanca.txt (raw text)
└── data/books/chess_fundamentals.json (structured, 240KB) ← NEW
```

---

## New/Modified API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/books` | GET | List available books with chapters and topics |
| `/api/chat` | POST | Now may include `suggested_action.lesson_plan` |

---

## Decisions Made

| # | Decision | Rationale |
|---|----------|-----------|
| 016 | Full context + prompt caching over RAG | Simpler, no retrieval errors, scales to 3 books |
| 017 | `[LESSON_PLAN]` marker in response | Single API call, clean separation of chat and data |

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `scripts/parse_book.py` | Created | Book parsing script |
| `data/books/chess_fundamentals.json` | Created | Structured book data (240KB) |
| `src/backend/books.py` | Created | Book library module |
| `src/backend/lesson.py` | Created | Lesson plan models and management |
| `src/backend/coach.py` | Modified | Book integration, lesson plan extraction, prompt caching |
| `src/backend/main.py` | Modified | Added /api/books endpoint, book library initialization |
| `src/frontend/chessboard.html` | Modified | Lesson plan display, active lesson banner |
| `docs/DECISIONS.md` | Modified | Added decisions 016-017 |
| `docs/PROGRESS.md` | Modified | Added Session 06 entry |

---

## Adding New Books

To add a new chess book:

1. Place the raw text file in `data/books/`
2. Create or modify `scripts/parse_book.py` to handle the new book's structure
3. Run the parser to generate a structured JSON file in `data/books/`
4. The `BookLibrary` auto-discovers JSON files on startup — no code changes needed

The JSON must follow the schema:
```json
{
  "metadata": { "title": "...", "author": "...", "year": ..., "total_sections": ..., "total_games": ... },
  "parts": [{ "chapters": [{ "sections": [{ "title": "...", "topics": [...], "content": "..." }] }] }],
  "illustrative_games": [{ "game_number": ..., "white": "...", "black": "...", "content": "..." }]
}
```

---

## Not Yet Implemented (Session 07)

- Claude controlling the board based on lesson plan
- Loading FEN positions from lesson plan onto the chessboard
- Real-time coaching commentary during practice activities
- Multi-PV move selection during coached play
