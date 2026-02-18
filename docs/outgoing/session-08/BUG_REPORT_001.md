# Bug Report: 500 Errors After Sustained Coach Interaction

> **Reported:** Session 09, February 18, 2026
> **Severity:** High — blocks coaching workflow entirely once triggered
> **Status:** Diagnosed, not yet fixed

---

## Summary

After several successful interactions in Coach Demo mode (a mix of `/api/chat` and `/api/coach/move` calls), the backend begins returning HTTP 500 errors on all subsequent requests. Once triggered, the failure persists until the rate limit window resets.

## Steps to Reproduce

1. Start the backend (`uvicorn main:app --port 8000`)
2. Open the frontend and begin a coaching conversation
3. Enter Coach Demo mode (Claude shows a position)
4. Make several moves in quick succession (5-10 moves over ~2 minutes)
5. Observe: requests start returning 500 errors

## Server Log Evidence

```
POST /api/coach/move HTTP/1.1" 200 OK    ← working
POST /api/coach/move HTTP/1.1" 200 OK    ← working
POST /api/coach/move HTTP/1.1" 200 OK    ← working
POST /api/coach/move HTTP/1.1" 500 Internal Server Error  ← fails
POST /api/coach/move HTTP/1.1" 500 Internal Server Error  ← all subsequent fail
POST /api/chat HTTP/1.1" 500 Internal Server Error        ← chat also fails
```

No Python tracebacks were printed — the `except Exception` blocks in `main.py` were catching errors and returning 500 responses without logging.

## Root Cause Analysis

**Most likely: Anthropic API rate limiting.**

- The book content included in the system prompt is ~57K tokens
- The org tier rate limit is ~30K input tokens/min
- Prompt caching (`cache_control: {"type": "ephemeral"}`) reduces this after the first call, but cached tokens still count at a reduced rate
- Each `/api/coach/move` request triggers a Claude API call (Stockfish analysis + coaching prompt)
- Rapid successive moves in Coach Demo mode can exhaust the rate limit budget
- Once the limit is hit, all Claude API calls fail until the window resets

**Contributing factor: No error visibility.**

The `except Exception` handlers in `main.py` converted errors to 500 responses but never logged the actual exception type or traceback. This made it impossible to confirm the root cause from the server terminal.

## Immediate Fix Applied (Session 09)

Added `logging` and `traceback` to all `except Exception` blocks in `main.py`:

```python
logger.error("Coach move failed:\n%s", traceback.format_exc())
```

This applies to the following endpoints:
- `POST /api/analyze`
- `POST /api/move`
- `POST /api/chat`
- `POST /api/coach/move`

The server will now print full tracebacks when 500 errors occur, confirming whether the error is `anthropic.RateLimitError` or something else.

## Potential Mitigation Strategies

These are initial ideas for discussion — not yet prioritized or decided upon.

| Strategy | Effort | Impact | Notes |
|----------|--------|--------|-------|
| Skip book content for `/api/coach/move` | Low | High | Move coaching relies on Stockfish data, not book content. Omitting the ~57K token book from these calls drastically reduces token usage. |
| Add retry with exponential backoff | Low | Medium | The Anthropic SDK supports automatic retries for rate limit errors. Smooths out burst usage. |
| Send only relevant book sections | Medium | High | Instead of the full book, include only the chapter/section relevant to the current topic. Lightweight RAG without infrastructure. |
| Upgrade API tier | None (cost) | High | Higher tiers have significantly larger rate limits. Simplest long-term fix. |
| Client-side rate limiting / debounce | Low | Medium | Prevent the frontend from sending moves faster than the API can handle. Show a cooldown indicator. |
| Surface rate limit errors to the user | Low | Medium | Catch `RateLimitError` specifically and return a 429 with a user-friendly message instead of a generic 500. |

## Related

- DECISION-006: Evaluations from White's perspective
- DECISION-023: Stockfish + Claude hybrid coaching
- SESSION_SUMMARY.md lines 219-222: Rate limiting noted as a known concern
