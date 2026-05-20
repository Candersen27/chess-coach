# Session 10 Tasks — Production Hosting (Fly.io)

> Execution order is chosen so we always have a working app before changing behavior:
> **A (single-origin) → C (Docker) → B (cost protection + meter) → D (deploy) → E (lock down + docs).**

---

## Task A: Single-origin serving

### A.1: Make Stockfish path configurable
In `src/backend/engine.py` ([line 16](../../../src/backend/engine.py#L16)):

- [ ] Default `engine_path` to `os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")`
- [ ] Import `os` if not already

### A.2: Make the frontend API base relative
In `src/frontend/chessboard.html` ([line 1714](../../../src/frontend/chessboard.html#L1714)):

- [ ] Change `const API_BASE_URL = 'http://localhost:8000'` → `const API_BASE_URL = ''`
- [ ] Confirm all 7 `fetch` sites use the constant (they do) so they become same-origin

### A.3: Serve the frontend from FastAPI
In `src/backend/main.py`:

- [ ] `from fastapi.staticfiles import StaticFiles`
- [ ] After all `/api/*` routes are declared, mount the frontend directory:
```python
from pathlib import Path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
```
- [ ] Ensure `chessboard.html` loads at `/` (rename to `index.html` **or** keep a tiny `index.html` redirect — pick one and note it)

**Verify:** `uvicorn main:app --port 8000`, open `http://localhost:8000/`. Board, analyze, play vs coach, batch all work from the served origin.

---

## Task C: Dockerize

### C.1: Dockerfile (project root)
- [ ] `FROM python:3.12-slim`
- [ ] `RUN apt-get update && apt-get install -y stockfish && rm -rf /var/lib/apt/lists/*` (lands at `/usr/games/stockfish`)
- [ ] Copy `src/` and `data/` preserving layout (book loader needs `<root>/data/books/`)
- [ ] `pip install --no-cache-dir -r src/backend/requirements.txt`
- [ ] Create + switch to a non-root user
- [ ] `EXPOSE 8000`
- [ ] `WORKDIR` at `src/backend`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends stockfish \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --no-cache-dir -r src/backend/requirements.txt
COPY src/ ./src/
COPY data/ ./data/
RUN useradd -m appuser && chown -R appuser /app
USER appuser
ENV STOCKFISH_PATH=/usr/games/stockfish
EXPOSE 8000
WORKDIR /app/src/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### C.2: .dockerignore (project root)
- [ ] `venv/`, `__pycache__/`, `*.pyc`, `.git/`, `PGN-files/`, `docs/`, `*.log`, `.env`

### C.3: Build & run locally
- [ ] `docker build -t chess-coach .`
- [ ] `docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY chess-coach`
- [ ] Open `http://localhost:8000/` — Stockfish analysis works; chat works with the key

**Verify:** Full app works inside the container.

---

## Task B: API-cost protection + token meter

### B.1: Per-request key in the coach
In `src/backend/coach.py`:

- [ ] Add optional `api_key: str | None = None` param to `chat_with_tools()` ([line 234](../../../src/backend/coach.py#L234))
- [ ] If `api_key` provided, build a transient `AsyncAnthropic(api_key=api_key, max_retries=2)` for that call; else use `self.client`
- [ ] Return token usage so the endpoint can record it (e.g. include `usage` = `response.usage.input_tokens + response.usage.output_tokens` in the returned dict)

### B.2: Budget guard module — `src/backend/budget.py`
- [ ] Per-IP daily token counter + global daily token counter, both keyed by current date (reset on date change)
- [ ] Env config: `PER_IP_TOKEN_CAP` (per-visitor allowance), `DAILY_TOKEN_CAP` (global ceiling)
- [ ] `check(ip) -> bool` — True if both the per-IP and global budgets have room
- [ ] `record(ip, tokens)` — add usage to both counters
- [ ] `status(ip) -> dict` — `{ "used": int, "cap": int, "remaining_pct": int }` for that IP

```python
from datetime import date
import os

class BudgetGuard:
    def __init__(self):
        self.per_ip_cap = int(os.getenv("PER_IP_TOKEN_CAP", "50000"))
        self.global_cap = int(os.getenv("DAILY_TOKEN_CAP", "300000"))
        self._day = date.today()
        self._per_ip: dict[str, int] = {}
        self._global = 0

    def _rollover(self):
        if date.today() != self._day:
            self._day = date.today()
            self._per_ip.clear()
            self._global = 0

    def check(self, ip: str) -> bool:
        self._rollover()
        return self._per_ip.get(ip, 0) < self.per_ip_cap and self._global < self.global_cap

    def record(self, ip: str, tokens: int):
        self._rollover()
        self._per_ip[ip] = self._per_ip.get(ip, 0) + tokens
        self._global += tokens

    def status(self, ip: str) -> dict:
        self._rollover()
        used = self._per_ip.get(ip, 0)
        remaining_pct = max(0, round(100 * (self.per_ip_cap - used) / self.per_ip_cap))
        return {"used": used, "cap": self.per_ip_cap, "remaining_pct": remaining_pct}
```

### B.3: Wire into chat endpoints
In `src/backend/main.py`, both `/api/chat` ([line 370](../../../src/backend/main.py#L370)) and `/api/coach/move` ([line 407](../../../src/backend/main.py#L407)):

- [ ] Add `request: Request` and read header `x-user-api-key`
- [ ] Get client IP (`request.client.host`; honor `Fly-Client-IP` / `X-Forwarded-For` first when present, since we're behind Fly's proxy)
- [ ] **BYOK path** (header present): pass key to `chat_with_tools(api_key=...)`, skip budget entirely, report `remaining_pct: null` / "unlimited"
- [ ] **Demo path** (no header): if `not guard.check(ip)` → return a `402`-style structured response `{ "error": "demo_budget_exhausted", "message": "..." }`. Otherwise run the call, then `guard.record(ip, usage)`
- [ ] On success, include `budget` = `guard.status(ip)` in the response body
- [ ] Instantiate one shared `BudgetGuard` at module load

### B.4: New endpoint `GET /api/budget`
- [ ] Returns `guard.status(ip)` for the caller (so the bar can render on page load)

### B.5: Frontend BYOK field
In `src/frontend/chessboard.html`:

- [ ] Add an "Anthropic API key (optional)" text input; persist to `localStorage` (`byok_key`)
- [ ] On the two chat fetches, send header `X-User-Api-Key` when a key is stored
- [ ] When a response is `demo_budget_exhausted`, show a message pointing at the BYOK field

### B.6: Token meter (progress bar + warnings)
In `src/frontend/chessboard.html`:

- [ ] Add a thin progress bar near the chat panel ("Demo budget: NN% left")
- [ ] On load, `GET /api/budget` → render bar. After each chat response, update from `data.budget.remaining_pct`
- [ ] Color: green > 35%, amber 10–35%, red < 10%
- [ ] One-time toasts: fire at first crossing of **≤35%** and **≤10%**; track `warned35` / `warned10` flags so each fires once per page session
- [ ] When BYOK key is active, hide the bar (or show "Using your key — unlimited")

**Verify:** Set `PER_IP_TOKEN_CAP` very low. Chat a few times → bar drains, 35% and 10% toasts fire once each, then `demo_budget_exhausted` prompts for a key. Paste a valid key → chat works, bar hidden.

---

## Task D: Deploy to Fly.io

- [ ] Install `flyctl`; `fly auth login`
- [ ] `fly launch --no-deploy` to generate `fly.toml`
- [ ] In `fly.toml`: `internal_port = 8000`, force HTTPS, set VM memory to **1024 MB** (Stockfish is hungry; 512 is tight)
- [ ] `fly secrets set ANTHROPIC_API_KEY=...`
- [ ] `fly secrets set PER_IP_TOKEN_CAP=... DAILY_TOKEN_CAP=...`
- [ ] `fly deploy`
- [ ] Open the `*.fly.dev` URL; smoke-test every feature (note: ~10s cold start after idle is expected)

---

## Task E: Lock down + docs

### E.1: CORS
In `src/backend/main.py` ([line 61](../../../src/backend/main.py#L61)):
- [ ] Set `allow_origins` to the `*.fly.dev` URL (same-origin makes CORS moot, but tighten anyway)

### E.2: Docs
- [ ] Add DECISION-024 … 027 to `docs/DECISIONS.md` (Fly.io, cost model, per-IP budget, in-memory tradeoff)
- [ ] Update `README.md`: live URL + "Deploy your own" (local Docker + `fly deploy`)
- [ ] Update `docs/PROGRESS.md` with the Session 10 summary
- [ ] Create `docs/outgoing/session-10/SESSION_SUMMARY.md`

---

## Deliverables Checklist

- [ ] `src/backend/engine.py` — `STOCKFISH_PATH` env support
- [ ] `src/frontend/chessboard.html` — relative API base, BYOK field, token meter
- [ ] `src/backend/main.py` — StaticFiles mount, budget wiring, `/api/budget`, tightened CORS
- [ ] `src/backend/coach.py` — per-request key + usage reporting
- [ ] `src/backend/budget.py` — NEW budget guard
- [ ] `Dockerfile` — NEW
- [ ] `.dockerignore` — NEW
- [ ] `fly.toml` — NEW (generated, then edited)
- [ ] Live `*.fly.dev` URL working
- [ ] Docs updated; git committed and pushed

---

## File Structure After Session

```
chess-coach/
├── Dockerfile                     # NEW
├── .dockerignore                  # NEW
├── fly.toml                       # NEW
├── data/                          # copied into image (books needed at runtime)
├── src/
│   ├── backend/
│   │   ├── main.py                # Modified — StaticFiles, budget, /api/budget, CORS
│   │   ├── coach.py               # Modified — per-request key + usage
│   │   ├── engine.py              # Modified — STOCKFISH_PATH env
│   │   └── budget.py              # NEW
│   └── frontend/
│       └── chessboard.html        # Modified — relative API base, BYOK, token meter
└── docs/
    ├── DECISIONS.md               # Updated (024–027)
    ├── PROGRESS.md                # Updated
    └── outgoing/session-10/       # NEW
```

---

## Notes for Claude Code

- **Order matters:** ship a working served app (A) and a working container (C) *before* touching cost logic (B). Don't change behavior on an app you can't yet load.
- **Mount StaticFiles last.** A catch-all `/` mount declared before the `/api/*` routes will shadow them.
- **Behind Fly's proxy, `request.client.host` is the proxy.** Use `Fly-Client-IP` (or `X-Forwarded-For`) for the real visitor IP, falling back to `request.client.host` locally — otherwise every visitor shares one bucket.
- **In-memory budget resets** on container restart/wake. That's an accepted tradeoff for a demo — don't over-engineer it into a DB this session.
- **Never commit the key.** It's already in `.gitignore` via `.env`; in prod it's a `fly secrets` value.
- **Keep the cap conservative to start** (`PER_IP_TOKEN_CAP` ~50K, `DAILY_TOKEN_CAP` ~300K) and tune after watching real spend.
- BYOK requests must **bypass** the budget entirely and report unlimited so the bar hides.
