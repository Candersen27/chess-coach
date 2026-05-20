# Hosting Plan — Go Live on Fly.io

> **Date:** 2026-05-20
> **Goal:** Get the chess coach running on a public HTTPS URL today, minimal scope.
> **Decisions made:**
> - **Platform:** Fly.io (reads our Dockerfile directly, free HTTPS + `*.fly.dev` URL)
> - **API cost:** Server key with a small daily spend cap **+** bring-your-own-key (BYOK) fallback
> - **Scope:** Critical path only. Defer the pytest suite and frontend-file-split (tracked in `HOSTING_READINESS.md`).

This builds on `HOSTING_READINESS.md`. Nothing on that checklist has been implemented yet, so this plan covers the four blockers: single-origin serving, API cost protection, Dockerization, and deployment.

---

## Phase A — Make the app deployable from one origin

Right now the frontend hardcodes `http://localhost:8000` and is opened as a local file. In production, FastAPI must serve the frontend itself so there's a single origin (this also makes CORS a non-issue).

- **A1.** Make the Stockfish path configurable. In [engine.py:16](../../src/backend/engine.py#L16), read `STOCKFISH_PATH` from env, defaulting to `/usr/games/stockfish` (the Debian apt install location, so the default works in our container too).
- **A2.** Make the frontend API base relative. In [chessboard.html:1714](../../src/frontend/chessboard.html#L1714), change `const API_BASE_URL = 'http://localhost:8000'` to `const API_BASE_URL = ''` so all `fetch` calls hit the serving origin. (7 call sites all use this constant.)
- **A3.** Serve the frontend from FastAPI. In [main.py](../../src/backend/main.py), add `from fastapi.staticfiles import StaticFiles` and mount `src/frontend/` at `/` with `html=True`, **after** all `/api/*` routes are declared. Rename `chessboard.html` access so the board loads at `/`.

**Verify:** `uvicorn main:app` then open `http://localhost:8000/` (not the file) — board, analysis, play mode all work against the same origin.

---

## Phase B — API cost protection (server cap + BYOK)

The coach client is built once from the env key ([coach.py:80](../../src/backend/coach.py#L80)). We need (1) a per-request key path for BYOK and (2) a daily spend cap so a public visitor can't run up the bill.

- **B1.** Refactor `ChessCoach` so the Anthropic client is selectable per request. Add an optional `api_key` param to `chat_with_tools(...)` ([coach.py:234](../../src/backend/coach.py#L234)): if provided, build a transient `AsyncAnthropic(api_key=...)`; otherwise use `self.client`. Keep the server key as the default.
- **B2.** Add a simple in-memory budget guard (new small module, e.g. `budget.py`):
  - **Per-IP** daily token counter (so each visitor sees their own remaining budget), plus a **global** daily token counter as a hard backstop. Both reset on date change.
  - Caps configured via env: `PER_IP_TOKEN_CAP` (the per-visitor demo allowance the bar reads from), `DAILY_TOKEN_CAP` (global ceiling, e.g. ~300K → roughly $1–2/day on Sonnet).
  - After each Claude call, add `response.usage` (input + output) tokens to both counters for that IP.
  - Expose a helper returning `{ used, cap, remaining_pct }` for a given IP.
  - *Caveat:* in-memory state resets when the container restarts — acceptable for a portfolio demo. SQLite/Redis is the future upgrade.
- **B3.** Wire the cap into the chat endpoints. In [main.py:370](../../src/backend/main.py#L370) (`/api/chat`) and [main.py:407](../../src/backend/main.py#L407) (`/api/coach/move`): read an `X-User-Api-Key` request header. If present → pass it through (BYOK, bypasses the cap entirely, reports unlimited). If absent → check the per-IP and global guards; when either is hit, return a structured `402`-style response telling the UI "daily demo budget reached — add your own key to continue." On success, **include the caller's budget state (`used` / `cap` / `remaining_pct`) in the response body** so the frontend bar updates after every message.
- **B4.** Frontend BYOK field. Add a small "Anthropic API key (optional)" input to [chessboard.html](../../src/frontend/chessboard.html), persisted in `localStorage`, sent as the `X-User-Api-Key` header on the two chat fetches. When the server returns the cap-reached response, surface a prompt pointing at that field.
- **B5.** Add a lightweight `GET /api/budget` endpoint returning the caller's `{ used, cap, remaining_pct }`. Lets the frontend show the bar on page load, before any chat has happened.

**Verify:** With no key entered and the cap set very low, chat returns the "add your key" message. Pasting a valid key makes chat work again, and the bar shows "unlimited" / hides for BYOK.

### B-bonus — Demo token meter (progress bar + low-budget warnings)

A visible indicator of how much of the per-IP demo budget remains, driven by the `remaining_pct` from B3/B5.

- **Bar:** A thin progress bar near the chat panel, e.g. "Demo budget: 72% left", color-shifting green → amber → red as it drains. Fetched once on load (`/api/budget`) and updated from each chat response.
- **Warnings:** Fire a one-time toast/banner when crossing **35%** ("Heads up — you've used most of the demo budget") and **10%** ("Almost out — add your own API key to keep chatting"). Track `warned35` / `warned10` flags in JS so each fires once per session, not on every message.
- **At 0%:** falls through to the existing B3 cap-reached prompt pointing at the BYOK field.
- **BYOK active:** hide the bar (or show "Using your key — unlimited"), since the cap doesn't apply.

*Effort: low — reuses the budget data already in the responses; pure frontend except for the `/api/budget` endpoint (B5).*

---

## Phase C — Dockerize

- **C1.** Add a `Dockerfile` at the project root:
  - `FROM python:3.12-slim`
  - `apt-get install -y stockfish` (lands at `/usr/games/stockfish`)
  - Copy `src/` and `data/` preserving the layout (book loader expects `<root>/data/books/` per [books.py:15](../../src/backend/books.py#L15)).
  - `pip install -r src/backend/requirements.txt`
  - Create and switch to a non-root user.
  - `EXPOSE 8000`, `CMD uvicorn main:app --host 0.0.0.0 --port 8000` (run from `src/backend`).
- **C2.** Add `.dockerignore`: `venv/`, `__pycache__/`, `.git/`, `PGN-files/`, `docs/`, `*.log`, `.env`.
- **C3.** Build & run locally: `docker build -t chess-coach . && docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$KEY chess-coach`, then hit `http://localhost:8000/`.

**Verify:** Full app works from the container — Stockfish analysis and (with key) chat.

---

## Phase D — Deploy to Fly.io

- **D1.** Install `flyctl` and `fly auth login`.
- **D2.** `fly launch --no-deploy` to generate `fly.toml`. Set `internal_port = 8000`, force HTTPS, and bump VM memory to **1GB** (512MB is tight once Stockfish spawns).
- **D3.** Set secrets (never committed): `fly secrets set ANTHROPIC_API_KEY=...`. Set cap config: `fly secrets set DAILY_TOKEN_CAP=... PER_IP_REQUESTS_PER_DAY=...`.
- **D4.** `fly deploy`. Open the `*.fly.dev` URL and smoke-test every feature.
  - *Note:* Fly apps auto-sleep when idle → ~10s cold start on the first hit. Fine for a portfolio demo.

---

## Phase E — Lock down & document

- **E1.** Tighten CORS in [main.py:61](../../src/backend/main.py#L61). Same-origin serving means CORS isn't strictly needed, but set `allow_origins` to the `*.fly.dev` URL instead of `["*"]`.
- **E2.** Update [README.md](../../README.md) with the live URL and a "Deploy your own" section (`docker compose up` for local, `fly deploy` for prod).

---

## Deferred (from HOSTING_READINESS.md — not blockers for today)

- Backend pytest suite (Priority 1) — highest resume signal, but a separate effort.
- Splitting `chessboard.html` into `index.html` / `styles.css` / `app.js` (Priority 4).
- Model upgrade from `claude-sonnet-4-20250514` to a current model.
- `docker-compose.yml` for one-command local dev (nice-to-have once the Dockerfile exists).

---

## Suggested order for today

1. Phase A (single-origin) — fastest win, unblocks everything.
2. Phase C (Docker) — get a working container before touching cost logic.
3. Phase B (cost protection) — the only feature-code change.
4. Phase D (deploy).
5. Phase E (lock down + docs).
