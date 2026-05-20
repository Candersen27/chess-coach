# Session 10 Summary - Production Hosting on Fly.io

> **Date:** May 20, 2026
> **Phase:** Deployment Readiness
> **Outcome:** Code complete & locally verified; Docker build + Fly deploy pending

---

## What Was Built

This session turned the localhost-only app into something deployable on a public HTTPS URL, with cost protection so a public visitor can try the Claude coaching without exposing the server's Anthropic key to runaway spend. It implements the four blockers from `docs/todo/HOSTING_READINESS.md`; the full plan is in `docs/todo/HOSTING_PLAN.md`.

**Decisions made:** Fly.io (container, not serverless) + server key with per-IP demo cap + BYOK fallback + minimal scope (defer tests and frontend-split). Logged as DECISION-024 … 027.

### Single-Origin Serving

**Stockfish path configurable (engine.py)**
- `ChessEngine.__init__` now defaults to `os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")`
- The default already matches the Debian apt install location used in the container

**Frontend served by FastAPI (main.py, frontend)**
- `app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True))`, declared **after** all `/api/*` routes so it doesn't shadow them
- Renamed `chessboard.html` → `index.html` so it loads at `/`
- `API_BASE_URL` changed from `'http://localhost:8000'` to `''` (same origin) — all 7 fetch sites now hit the serving origin
- Verified: page, `/api/health`, `chessboard-1.0.0.min.{js,css}`, and piece PNGs all return 200 from one origin

### API-Cost Protection (Server Cap + BYOK)

**Budget guard (budget.py — new)**
- `BudgetGuard`: per-IP daily token counter + global daily ceiling, in-memory, resets on calendar-day change
- `check(ip)`, `record(ip, tokens)`, `status(ip) -> {used, cap, remaining_pct}`
- `tokens_charged(usage)` counts `input + output + cache_creation` and **skips cache reads** (billed ~0.1x — charging them would drain a visitor's bar for near-free tokens)
- `client_ip(request)` resolves the real visitor IP from `Fly-Client-IP` / `X-Forwarded-For`, falling back to the socket peer
- Defaults: `PER_IP_TOKEN_CAP=150000`, `DAILY_TOKEN_CAP=1000000` (sized so the ~57K one-time book cache-write doesn't exhaust a visitor in one message)

**Per-request key (coach.py)**
- `chat_with_tools(..., api_key=None)` — when a key is passed, builds a transient `AsyncAnthropic` for that call; otherwise uses the shared server client

**Endpoint wiring (main.py)**
- `/api/chat` and `/api/coach/move` read the `X-User-Api-Key` header
- BYOK present → pass key through, bypass budget, report `{"unlimited": true}`
- No key → `guard.check(ip)`; if exhausted, return `402` with `{error: "demo_budget_exhausted", message, budget}`; else run, then `guard.record(ip, tokens_charged(usage))` and attach `budget` status
- New `GET /api/budget` returns the caller's status (so the meter renders on load)
- CORS made env-configurable via `ALLOWED_ORIGINS` (default `*`)

### Demo Token Meter (Progress Bar + Warnings)

**Frontend (index.html)**
- Thin progress bar near chat ("Demo budget: NN% left"); fill color green > 35%, amber 10–35%, red < 10%
- One-time toasts at ≤35% and ≤10% remaining, tracked with `budgetWarned35` / `budgetWarned10`
- BYOK key field (password input) persisted to `localStorage`; `coachHeaders()` attaches it to both chat fetches
- Both fetches handle `402` by calling `handleBudgetExhausted()` (message + focus the key field) instead of erroring
- Bar hides when a BYOK key is active; `fetchBudget()` + `refreshByokStatus()` run on page load

### Dockerization

**Dockerfile + .dockerignore (new, project root)**
- `python:3.12-slim`, `apt-get install stockfish`, deps installed before source for layer caching, copies `src/` + `data/` preserving layout (book loader needs `<root>/data/books/`), non-root `appuser`, `EXPOSE 8000`, runs uvicorn from `src/backend`
- `.dockerignore` excludes `venv/`, `__pycache__/`, `.git/`, `.env`, `docs/`, `PGN-files/`, logs

---

## Verification

All testable-without-Docker paths were exercised against a running server:

| Check | Result |
|---|---|
| Page + API + assets from one origin | ✅ 200 |
| `budget.py` unit logic (rollover, caps, `tokens_charged` excludes cache reads) | ✅ |
| `GET /api/budget` | ✅ returns snapshot |
| `POST /api/chat`, no key, cap=0 | ✅ `402 demo_budget_exhausted`, no Claude call |
| `POST /api/chat`, BYOK header, cap=0 | ✅ bypassed gate, attempted real call (401 on dummy key) |
| App boots with default caps | ✅ no startup errors |

**Not verified (no Docker/flyctl/real key in the dev environment):** the Docker image build, the Fly deploy, and a successful live Claude call. The code paths for all three are in place.

---

## How to Finish Deployment

See `docs/incoming/session-10/TASKS.md` Task D for the full runbook. Short version:

```bash
# 1. Local container test (Docker running)
docker build -t chess-coach .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$YOUR_KEY chess-coach

# 2. Deploy
fly launch --no-deploy            # edit fly.toml: internal_port 8000, vm memory 1024
fly secrets set ANTHROPIC_API_KEY=$YOUR_KEY
fly secrets set PER_IP_TOKEN_CAP=150000 DAILY_TOKEN_CAP=1000000
fly deploy

# 3. After live
fly secrets set ALLOWED_ORIGINS=https://your-app.fly.dev
```

**Most likely first-build snag:** the apt Stockfish package name / binary path. If `/usr/games/stockfish` isn't where it lands, set `STOCKFISH_PATH` accordingly.

---

## Files Changed

| File | Change |
|------|--------|
| `src/backend/engine.py` | `STOCKFISH_PATH` env support |
| `src/backend/coach.py` | `chat_with_tools(api_key=...)` for BYOK |
| `src/backend/budget.py` | **New** — budget guard, `tokens_charged`, `client_ip` |
| `src/backend/main.py` | StaticFiles mount, budget wiring, `/api/budget`, env CORS |
| `src/frontend/index.html` | **Renamed** from chessboard.html; relative API base, BYOK field, token meter |
| `Dockerfile`, `.dockerignore` | **New** |
| `docs/DECISIONS.md` | DECISION-024 … 027 |
| `docs/PROGRESS.md` | Session 10 entry |
| `docs/incoming/session-10/`, `docs/todo/HOSTING_PLAN.md` | Planning docs |

---

## Deferred (tracked in HOSTING_READINESS.md)

- pytest suite (Priority 1)
- Split `index.html` into `index.html` / `styles.css` / `app.js` (Priority 4)
- Persistent (DB-backed) budget tracking
- Model upgrade from `claude-sonnet-4-20250514`
