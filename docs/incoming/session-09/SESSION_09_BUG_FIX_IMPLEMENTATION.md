# Session 09: Rate Limit Bug Fix - Implementation Guide

> **Date:** February 18, 2026
> **Target:** Fix HTTP 500 errors caused by rate limiting during sustained Coach Demo usage
> **Files to modify:** `src/backend/coach.py`, `src/backend/main.py`
> **Complexity:** Low - straightforward changes to existing code

---

## Problem Summary

After several rapid interactions in Coach Demo mode, the backend returns HTTP 500 errors on all subsequent requests. Root cause: Anthropic API rate limiting due to ~57K token book content being sent with every `/api/coach/move` request.

**For full context, see:** `BUG_REPORT_001.md`

---

## Solution Overview

Implement three complementary fixes:

1. **Skip book content for move coaching** (primary fix - 95% token reduction)
2. **Add automatic retries** (smooth out temporary rate limit spikes)
3. **Better error handling** (surface rate limit errors with 429 instead of 500)

---

## Implementation Tasks

### Task 1: Modify Book Context Injection

**File:** `src/backend/coach.py`

**Goal:** Make book context optional in the coaching system prompt. Skip it for move coaching, keep it for conversational coaching.

**Current state:** Book content is always included in system prompt via `BookLibrary`.

**Changes needed:**

```python
# Add parameter to control book inclusion
async def chat(
    message: str, 
    context: dict = None,
    include_book: bool = True  # NEW: Make book inclusion optional
) -> dict:
    """
    Chat with the AI coach.
    
    Args:
        message: User's message
        context: Optional context (game state, patterns, etc.)
        include_book: Whether to include book content in system prompt (default: True)
    """
    # Build system prompt
    system_prompt = BASE_COACHING_PERSONA
    
    # NEW: Conditionally include book
    if include_book:
        system_prompt += "\n\n" + book_library.get_system_prompt_content()
    
    # Add pattern context if available
    if context and context.get("patterns"):
        system_prompt += f"\n\nPattern Analysis:\n{context['patterns']}"
    
    # ... rest of existing logic
```

**Similar changes for:** `analyze_move_with_coaching()` or any other function that builds coaching prompts.

---

### Task 2: Update `/api/coach/move` to Skip Book

**File:** `src/backend/main.py`

**Goal:** Pass `include_book=False` when calling coach functions from the move endpoint.

**Current state:**
```python
@app.post("/api/coach/move")
async def coach_move(move_data: dict):
    try:
        # ... existing move processing ...
        
        # Get coaching response
        coaching_response = await coach.chat(
            message=coaching_prompt,
            context=context
        )
```

**Change to:**
```python
@app.post("/api/coach/move")
async def coach_move(move_data: dict):
    try:
        # ... existing move processing ...
        
        # Get coaching response (skip book for move-by-move coaching)
        coaching_response = await coach.chat(
            message=coaching_prompt,
            context=context,
            include_book=False  # NEW: Skip book content for move coaching
        )
```

**Why:** Move coaching relies on Stockfish analysis, not book references. This reduces token usage from ~57K → ~3K per request.

**Keep book for `/api/chat`:** The conversational coaching endpoint should continue passing `include_book=True` (or use the default).

---

### Task 3: Add Automatic Retries to Anthropic Client

**File:** `src/backend/coach.py`

**Goal:** Enable the Anthropic SDK's built-in retry logic for rate limit errors.

**Current state:**
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

**Change to:**
```python
from anthropic import Anthropic

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_retries=2  # NEW: Automatic retry with exponential backoff
)
```

**Why:** The SDK handles exponential backoff automatically for transient rate limit errors. This smooths out burst usage without custom retry logic.

---

### Task 4: Add Specific Rate Limit Error Handling

**File:** `src/backend/main.py`

**Goal:** Catch `RateLimitError` specifically and return HTTP 429 with helpful message instead of generic 500.

**Current state:**
```python
@app.post("/api/coach/move")
async def coach_move(move_data: dict):
    try:
        # ... logic ...
    except Exception as e:
        logger.error("Coach move failed:\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process move"}
        )
```

**Change to:**
```python
from anthropic import RateLimitError  # NEW: Import specific error type

@app.post("/api/coach/move")
async def coach_move(move_data: dict):
    try:
        # ... logic ...
    except RateLimitError as e:  # NEW: Catch rate limit errors specifically
        logger.warning("Rate limit hit: %s", str(e))
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit reached. Please wait a moment and try again.",
                "retry_after": 60  # Suggest waiting 60 seconds
            }
        )
    except Exception as e:
        logger.error("Coach move failed:\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process move"}
        )
```

**Apply this pattern to:**
- `POST /api/coach/move`
- `POST /api/chat`
- `POST /api/analyze` (if it uses Claude)

**Why:** Users get clear feedback instead of mysterious 500 errors, and can take appropriate action (wait and retry).

---

## Testing Checklist

After implementing changes:

- [ ] Start backend with `uvicorn main:app --port 8000`
- [ ] Open frontend and enter Coach Demo mode
- [ ] Make 5-10 rapid moves in succession
- [ ] Verify: Moves continue working (no 500 errors)
- [ ] Monitor server logs: Confirm token usage is reduced (~3K instead of ~57K per move)
- [ ] Test conversational coaching in `/api/chat`: Verify book content is still included
- [ ] Intentionally trigger rate limit (if possible): Verify 429 response with helpful message

---

## Expected Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Tokens per `/api/coach/move` | ~57,000 | ~3,000 |
| Token reduction | - | 95% |
| Moves before rate limit | ~5-10 | ~50-100 (estimated) |
| Error visibility | 500 (generic) | 429 (specific) |
| Retry handling | Manual | Automatic |
| Book in conversational chat | Yes | Yes (unchanged) |
| Book in move coaching | Yes | No (intentional) |

---

## Code Quality Notes

**Error handling:**
- Keep the traceback logging added previously (`logger.error(..., traceback.format_exc())`)
- Add the specific `RateLimitError` handling BEFORE the generic `Exception` handler
- Consider adding similar specific error handling for other Anthropic exceptions (`APIError`, `APIConnectionError`, etc.) in future sessions

**Book context management:**
- The `include_book` parameter makes this explicit and testable
- Consider adding a comment in `main.py` explaining why move coaching skips the book
- Future: Could make this configurable via environment variable if needed

**Backwards compatibility:**
- `include_book=True` as default preserves existing behavior
- Only `/api/coach/move` opts out explicitly

---

## Related Decisions

This fix aligns with existing architecture:

- **DECISION-023:** Stockfish + Claude hybrid coaching → Move coaching focuses on Stockfish analysis, so book isn't needed
- **DECISION-016:** Full context + prompt caching over RAG → We're not abandoning this; just being smart about when book content adds value
- **DECISION-010:** Frontend manages state → No state changes needed; this is purely backend optimization

---

## Success Criteria

✅ Session 09 succeeds when:
1. Rapid moves in Coach Demo mode no longer trigger 500 errors
2. Token usage per move coaching request is reduced by ~90%
3. Conversational coaching still has full book access
4. Rate limit errors (if they occur) return 429 with helpful message
5. Server logs show clear error tracebacks for debugging

---

## Notes for Implementation

- The changes are intentionally surgical - modify behavior, don't restructure
- Book library code stays unchanged - we're just controlling when it's used
- This is a hotfix for immediate pain, not a complete redesign
- If rate limits persist even after these changes, Phase 2 solutions (client-side debouncing, API tier upgrade) can be added later

---

*Document prepared: February 18, 2026*
*Target: Claude Code for Session 09 implementation*
