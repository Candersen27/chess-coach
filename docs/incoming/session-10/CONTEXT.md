# Session 10 Context — Production Hosting (Fly.io)

> **Date:** May 20, 2026
> **Phase:** Deployment Readiness
> **Session Goal:** Get the chess coach running on a public HTTPS URL, with API-cost protection so a public visitor can't run up the Anthropic bill.

---

## Where This Fits

| Session | Focus | Status |
|---------|-------|--------|
| 08 | Board control via tool calling + Coach Demo | ✅ Complete |
| 09 | Rate-limit resilience, draw offers, PGN context | ✅ Complete |
| **10** | **Production hosting on Fly.io + cost protection** | **This Session** |

This session implements the four blockers identified in `docs/todo/HOSTING_READINESS.md`. The full ordered plan lives in **`docs/todo/HOSTING_PLAN.md`** — this CONTEXT/TASKS pair is the executable version of it.

**Scope decision: minimal.** Get it live today. The pytest suite (Readiness Priority 1) and the frontend file-split (Priority 4) are explicitly deferred — they remain tracked in `HOSTING_READINESS.md`.

---

## What Exists

### Backend (`src/backend/`)
- `main.py` — FastAPI app. CORS is `allow_origins=["*"]` ([main.py:61](../../../src/backend/main.py#L61)). Endpoints: `/api/health`, `/api/analyze`, `/api/move`, `/api/game/analyze`, `/api/games/analyze-batch`, `/api/chat`, `/api/coach/move`, `/api/books`.
- `coach.py` — `ChessCoach` builds one `AsyncAnthropic` client from the env key in `__init__` ([coach.py:80](../../../src/backend/coach.py#L80)). `chat_with_tools()` ([coach.py:234](../../../src/backend/coach.py#L234)) is the main entry. Model: `claude-sonnet-4-20250514`.
- `engine.py` — Stockfish path hardcoded to `/usr/games/stockfish` ([engine.py:16](../../../src/backend/engine.py#L16)).
- `books.py` — loads book JSON from `<root>/data/books/` ([books.py:15](../../../src/backend/books.py#L15)). The image must preserve the `src/` + `data/` layout.

### Frontend (`src/frontend/`)
- `chessboard.html` — 2900-line single file. `const API_BASE_URL = 'http://localhost:8000'` ([chessboard.html:1714](../../../src/frontend/chessboard.html#L1714)), used by 7 `fetch` call sites. Opened directly as a local file today.

### What's missing (this session adds it)
- No Dockerfile. No static-file serving from FastAPI. No API-cost protection. Runs localhost-only.

---

## What We're Building This Session

### 1. Single-origin serving
FastAPI serves the frontend itself, so there's one origin in production. This makes the frontend work when deployed *and* makes CORS a non-issue.

### 2. API-cost protection: server cap + BYOK hybrid
- Visitors get a real taste of Claude coaching **on the server's key**, capped by a small daily token budget.
- Budget is tracked **per-IP** (so each visitor sees their own remaining allowance), with a **global** daily ceiling as a hard backstop.
- When a visitor's budget is exhausted, the UI invites them to paste **their own** Anthropic key (BYOK), which bypasses the cap.

### 3. Demo token meter (progress bar + warnings)
- A thin progress bar near the chat: "Demo budget: 72% left", green → amber → red.
- One-time toasts at **35%** and **10%** remaining.
- Driven by `remaining_pct` returned in chat responses and a new `GET /api/budget`.

### 4. Dockerize + deploy to Fly.io
- Dockerfile with apt Stockfish, non-root user, port 8000.
- `fly launch` / `fly deploy`; secrets via `fly secrets`.

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Platform | Fly.io | Reads our Dockerfile directly, free HTTPS + `*.fly.dev` URL, supports the Stockfish subprocess (serverless can't) |
| Cost model | Server key + small daily cap, BYOK fallback | Reviewers see Claude coaching live without setup; cost is capped; heavy users bring their own key |
| Budget scope | Per-IP token counter + global ceiling | "Tokens *you* have left" is accurate per visitor; global cap protects the wallet |
| Budget storage | In-memory | Simplest; resets on container restart/wake — acceptable for a portfolio demo. SQLite/Redis is the future upgrade |
| Frontend serving | FastAPI `StaticFiles` | One origin → frontend works in prod + no CORS config needed |
| Stockfish path | `STOCKFISH_PATH` env, default `/usr/games/stockfish` | Default already matches the Debian apt install location in the container |

These become DECISION-024 … DECISION-027 in `docs/DECISIONS.md` (last existing is DECISION-023).

---

## Cost Math (for setting the cap)

- Sonnet pricing dominated by the ~57K-token cached book prefix (90% discount after first call) + per-message input/output.
- Target: cap global spend around **$1–2/day**. Start with `DAILY_TOKEN_CAP` ≈ 300K tokens and `PER_IP_TOKEN_CAP` ≈ 40–60K (a handful of coaching exchanges per visitor). Tune after watching real usage.

---

## Success Criteria

1. App loads at a public `https://<app>.fly.dev/` URL — board, analysis, play, batch all work.
2. Frontend talks to its own origin (no `localhost` references remain).
3. Stockfish runs in the container.
4. Chat works on the server key until the per-IP cap is hit, then prompts for BYOK.
5. Pasting a valid key in the BYOK field restores chat and bypasses the cap.
6. Token meter shows remaining %, updates after each message, and fires the 35% / 10% warnings once each.
7. `ANTHROPIC_API_KEY` is a Fly secret, never committed.

---

## Out of Scope (deferred, not blockers)

- pytest suite (Readiness Priority 1)
- Splitting `chessboard.html` into `index.html` / `styles.css` / `app.js` (Readiness Priority 4)
- Persistent (DB-backed) budget tracking
- Model upgrade from `claude-sonnet-4-20250514`
- `docker-compose.yml` for one-command local dev (nice-to-have once the Dockerfile exists)

---

## Reference Files

- `docs/todo/HOSTING_PLAN.md` — the ordered plan this session executes
- `docs/todo/HOSTING_READINESS.md` — original strategic review
- `src/backend/coach.py`, `src/backend/main.py`, `src/backend/engine.py`, `src/backend/books.py`
- `src/frontend/chessboard.html`
