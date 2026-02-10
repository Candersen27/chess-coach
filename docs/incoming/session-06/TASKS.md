# Session 06 Tasks - Lesson Plan Generation + Book Integration

---

## Task 1: Parse Chess Fundamentals into Structured JSON

### 1.1: Create Book Parser Script

Create `scripts/parse_book.py`:

- [ ] Read `data/books/chess_fundamentals_capablanca.txt`
- [ ] Strip Project Gutenberg header/footer
- [ ] Identify and extract:
  - Parts (PART I, PART II)
  - Chapters (CHAPTER I, II, etc.)
  - Sections (numbered: 1. SOME SIMPLE MATES, etc.)
  - Illustrative games (GAME 1, 2, etc.)
- [ ] Extract topics/keywords for each section (for future search)
- [ ] Handle the descriptive notation (K-B6 style) — keep as-is, Claude understands it
- [ ] Output structured JSON

**Parsing hints:**
```python
# Part markers
r'^PART [IVX]+$'

# Chapter markers  
r'^CHAPTER [IVX]+$'

# Section markers (numbered content sections)
r'^\d+\.\s+[A-Z][A-Z\s]+$'  # e.g., "1. SOME SIMPLE MATES"

# Game markers in Part II
r'^GAME\.' or starts with game number and opening name

# Section separators
r'^\s*\*\s+\*\s+\*\s+\*\s+\*\s*$'  # The "* * * * *" dividers
```

### 1.2: Create Structured JSON Output

Output to `data/books/chess_fundamentals.json`:

```json
{
  "metadata": {
    "title": "Chess Fundamentals",
    "author": "José Raúl Capablanca",
    "year": 1921,
    "source": "Project Gutenberg",
    "total_sections": 33,
    "total_games": 13
  },
  "parts": [
    {
      "part_number": 1,
      "title": "Instructional Content",
      "chapters": [
        {
          "chapter_number": 1,
          "title": "First Principles: Endings, Middle-game and Openings",
          "sections": [
            {
              "section_number": 1,
              "title": "Some Simple Mates",
              "topics": ["rook endgame", "two bishops", "queen mate", "basic checkmate"],
              "content": "The actual text content...",
              "examples": ["EXAMPLE 1...", "EXAMPLE 2..."]
            }
          ]
        }
      ]
    }
  ],
  "illustrative_games": [
    {
      "game_number": 1,
      "event": "Match, 1909",
      "white": "F. J. Marshall",
      "black": "J. R. Capablanca",
      "opening": "Queen's Gambit Declined",
      "content": "Full game with annotations..."
    }
  ]
}
```

### 1.3: Verify Parser Output

- [ ] Run parser: `python scripts/parse_book.py`
- [ ] Check all 33 sections extracted
- [ ] Check all 13+ games extracted
- [ ] Spot-check content accuracy
- [ ] Verify JSON is valid

---

## Task 2: Create Book Integration Module

### 2.1: Create books.py

Create `src/backend/books.py`:

- [ ] `BookLibrary` class to manage chess books
- [ ] Load structured JSON on initialization
- [ ] `get_full_content()` — returns entire book as formatted text (for prompt)
- [ ] `get_section(chapter, section)` — get specific section
- [ ] `search_topics(keywords)` — basic keyword search (for Level 2 scaling)
- [ ] `get_relevant_content(topic, max_tokens)` — future method for selective retrieval

```python
class BookLibrary:
    def __init__(self, books_dir: str = "data/books"):
        self.books = {}
        self._load_books(books_dir)
    
    def get_full_content(self, book_title: str) -> str:
        """Get entire book formatted for prompt inclusion."""
        pass
    
    def get_section(self, book_title: str, section_number: int) -> dict:
        """Get a specific section by number."""
        pass
    
    def search_topics(self, keywords: List[str]) -> List[dict]:
        """Find sections matching keywords (basic search)."""
        pass
    
    def format_for_prompt(self, book_title: str) -> str:
        """Format book content for Claude's system prompt."""
        pass
```

### 2.2: Format Book for Prompt

Create a clean format that Claude can reference:

```
=== CHESS FUNDAMENTALS by José Raúl Capablanca (1921) ===

PART I: INSTRUCTIONAL CONTENT

CHAPTER 1: First Principles

Section 1: Some Simple Mates
----------------------------
[content]

Section 2: Pawn Promotion
-------------------------
[content]

...

PART II: ILLUSTRATIVE GAMES

Game 1: Marshall vs Capablanca (Queen's Gambit Declined, 1909)
--------------------------------------------------------------
[content]
```

---

## Task 3: Create Lesson Plan Module

### 3.1: Create lesson.py

Create `src/backend/lesson.py`:

- [ ] `LessonPlan` Pydantic model
- [ ] `LessonActivity` model with activity types
- [ ] `LessonManager` class for plan generation and tracking

```python
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class Position(BaseModel):
    fen: str
    instruction: str
    goal: Optional[str] = None
    hints: List[str] = []

class LessonActivity(BaseModel):
    type: Literal["practice_game", "position_study", "tactics_drill", "endgame_practice", "game_review"]
    positions: List[Position] = []
    coach_plays: Optional[Literal["white", "black"]] = None
    target_opening: Optional[str] = None
    pgn: Optional[str] = None  # For game review

class SourceReference(BaseModel):
    book: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_hint: Optional[str] = None

class LessonPlan(BaseModel):
    id: str
    created_at: datetime
    topic: str
    type: str
    source_reference: Optional[SourceReference] = None
    goals: List[str]
    activity: LessonActivity
    teaching_notes: List[str] = []
    success_criteria: Optional[str] = None

class LessonManager:
    def __init__(self):
        self.current_lesson: Optional[LessonPlan] = None
        self.lesson_history: List[LessonPlan] = []
    
    def create_lesson_from_response(self, claude_response: dict) -> LessonPlan:
        """Parse Claude's lesson plan from response."""
        pass
    
    def get_current_lesson(self) -> Optional[LessonPlan]:
        """Get active lesson plan."""
        pass
    
    def complete_lesson(self, success: bool, notes: str = ""):
        """Mark current lesson complete."""
        pass
```

---

## Task 4: Update Coach with Book Integration

### 4.1: Modify coach.py

- [ ] Import `BookLibrary` from books.py
- [ ] Load book library on coach initialization
- [ ] Update system prompt to include book content
- [ ] Add lesson plan generation capability

**Updated system prompt structure:**

```python
SYSTEM_PROMPT = """You are a friendly, knowledgeable chess coach helping a student improve.

Your approach:
- Ask questions to understand what the student wants to work on
- Give concrete, actionable advice using specific positions
- Reference the chess literature when relevant
- Be encouraging but honest about mistakes
- When the student is ready to practice, generate a structured lesson plan

You have access to classic chess literature to ground your teaching:

{book_content}

When the student agrees to practice something, generate a lesson plan in this JSON format:
```json
{{
  "topic": "...",
  "type": "endgame_practice|position_study|practice_game|tactics_drill|game_review",
  "source_reference": {{"book": "...", "section": "..."}},
  "goals": ["...", "..."],
  "activity": {{
    "type": "...",
    "positions": [{{"fen": "...", "instruction": "...", "goal": "..."}}]
  }},
  "teaching_notes": ["...", "..."],
  "success_criteria": "..."
}}
```

Only generate a lesson plan when the student explicitly agrees to practice.
Include the lesson plan JSON at the end of your message, after [LESSON_PLAN].

Current board state: {board_context}
"""
```

### 4.2: Parse Lesson Plan from Response

- [ ] Check if response contains `[LESSON_PLAN]` marker
- [ ] Extract JSON after marker
- [ ] Validate against LessonPlan model
- [ ] Return in `suggested_action` field

```python
async def chat(self, message: str, conversation_history: list, board_context: dict) -> dict:
    response = await self._call_claude(message, conversation_history, board_context)
    
    lesson_plan = None
    clean_message = response
    
    if "[LESSON_PLAN]" in response:
        parts = response.split("[LESSON_PLAN]")
        clean_message = parts[0].strip()
        try:
            plan_json = extract_json(parts[1])
            lesson_plan = LessonPlan(**plan_json)
        except:
            pass  # Failed to parse, continue without lesson
    
    return {
        "message": clean_message,
        "suggested_action": {
            "type": "start_lesson",
            "lesson_plan": lesson_plan.dict()
        } if lesson_plan else None
    }
```

---

## Task 5: Update API Models

### 5.1: Update main.py

- [ ] Add `LessonPlan` to response models
- [ ] Update `ChatResponse` to include lesson plan
- [ ] Add lesson-related endpoints if needed

```python
class SuggestedAction(BaseModel):
    type: Literal["start_lesson", "set_position", "load_pgn"]
    lesson_plan: Optional[LessonPlan] = None
    fen: Optional[str] = None
    pgn: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    suggested_action: Optional[SuggestedAction] = None
```

---

## Task 6: Frontend - Handle Lesson Plans

### 6.1: Update Chat Handler

- [ ] Check response for `suggested_action`
- [ ] If lesson plan received, display confirmation
- [ ] Store lesson plan in JavaScript for Session 07

```javascript
async function sendMessage() {
    // ... existing code ...
    
    const data = await response.json();
    displayCoachMessage(data.message);
    
    if (data.suggested_action?.type === 'start_lesson') {
        currentLessonPlan = data.suggested_action.lesson_plan;
        displayLessonConfirmation(currentLessonPlan);
    }
}

function displayLessonConfirmation(plan) {
    // Show lesson goals and ask user to confirm start
    const confirmMsg = `
        Ready to start: ${plan.topic}
        
        Goals:
        ${plan.goals.map(g => '• ' + g).join('\n')}
        
        Type "start" when ready, or ask questions first.
    `;
    displayCoachMessage(confirmMsg);
}
```

### 6.2: Display Lesson Info (Basic)

- [ ] Show current lesson topic/goals when active
- [ ] Indicate lesson mode vs free mode
- [ ] Store lesson plan for Session 07 board integration

---

## Task 7: Testing

### 7.1: Book Integration Tests

- [ ] Verify book loads correctly
- [ ] Test `get_section()` returns correct content
- [ ] Test `search_topics()` finds relevant sections
- [ ] Verify prompt formatting is clean

### 7.2: Lesson Generation Tests

Test conversations that should generate lessons:

```bash
# Test 1: Endgame lesson request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to practice rook endgames. Let'\''s do it.",
    "conversation_history": [
      {"role": "user", "content": "I keep losing rook endgames"},
      {"role": "assistant", "content": "Rook endgames are crucial! Would you like to practice the Lucena position?"}
    ],
    "board_context": null
  }'

# Verify response contains lesson_plan in suggested_action
```

### 7.3: Book Reference Tests

- [ ] Ask about endgames → should reference Capablanca
- [ ] Ask about piece values → should cite book
- [ ] Ask about openings → should reference relevant sections

---

## Task 8: Documentation

### 8.1: Update Project Docs

- [ ] Add DECISION-016: Full context + caching over RAG
- [ ] Add DECISION-017: Lesson plan JSON structure
- [ ] Update PROGRESS.md with Session 06 summary
- [ ] Document book parsing pipeline in code comments

### 8.2: Create Session 06 Outgoing Docs

- [ ] `docs/outgoing/session-06/SESSION_SUMMARY.md`
- [ ] `docs/outgoing/session-06/README.md`
- [ ] Document how to add new books

---

## Deliverables Checklist

- [ ] `scripts/parse_book.py` — Book parsing script
- [ ] `data/books/chess_fundamentals.json` — Structured book data
- [ ] `src/backend/books.py` — Book library module
- [ ] `src/backend/lesson.py` — Lesson plan module
- [ ] `src/backend/coach.py` — Updated with book + lesson support
- [ ] `src/backend/main.py` — Updated response models
- [ ] `src/frontend/chessboard.html` — Basic lesson plan handling
- [ ] Coach naturally references Capablanca in responses
- [ ] Lesson plans generate when user agrees to practice
- [ ] Documentation updated
- [ ] Git committed and pushed

---

## File Structure After Session

```
chess-coach/
├── scripts/
│   └── parse_book.py              # NEW - book parsing
├── data/
│   └── books/
│       ├── chess_fundamentals_capablanca.txt  # Raw text
│       └── chess_fundamentals.json            # NEW - structured
├── src/
│   └── backend/
│       ├── main.py                # Modified
│       ├── coach.py               # Modified
│       ├── engine.py              # Unchanged
│       ├── books.py               # NEW
│       └── lesson.py              # NEW
└── docs/
    ├── DECISIONS.md               # Updated
    ├── PROGRESS.md                # Updated
    └── outgoing/session-06/       # NEW
```

---

## Notes for Claude Code

- The book uses **descriptive notation** (K-B6, not Kf6). Keep it as-is — Claude understands both.
- **Don't build RAG.** Use full context + prompt caching. Simpler and better for this scale.
- The `[LESSON_PLAN]` marker approach keeps Claude's conversational response separate from structured data.
- Lesson plans are **not executed yet** — that's Session 07. This session just generates them.
- Book content in prompt will be large (~65K tokens). That's fine — prompt caching handles the cost.
- Test that Claude actually references Capablanca, not just generic advice.
