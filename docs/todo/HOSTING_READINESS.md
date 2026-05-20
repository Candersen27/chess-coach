# Hosting Readiness — Strategic Recommendations

> **Date:** 2026-02-23
> **Context:** The chess coach project is approaching the point where it can be hosted publicly as a portfolio/resume piece. A code review identified the following priorities to address before deployment.
> **Goal:** Make the project hostable, secure, and impressive to technical reviewers.

---

## Current State

The backend architecture is solid: FastAPI + async Stockfish + Claude API with tool calling, prompt caching, and a hybrid engine/LLM coaching pipeline. The frontend is a functional 2900-line single HTML file with embedded JS/CSS. There are 23 documented architecture decisions, a progress log covering 9 development sessions, and features including game analysis, batch pattern detection, play-vs-coach mode, chat coaching with board control, and book integration.

**What's strong and resume-worthy already:**
- Stockfish + Claude hybrid architecture (engine for accuracy, LLM for explanation)
- Native Anthropic tool calling for board control (`set_board_position`, `start_game`)
- Prompt caching strategy for book content (~57K tokens cached at 90% discount)
- Batch game analysis with tactical pattern detection and phase performance
- Well-documented decision log (DECISIONS.md) showing engineering reasoning

---

## Priority 1: Backend Tests (Highest resume signal per effort)

**Problem:** There are zero tests in the project. This is the first thing a senior engineer or technical interviewer looks for. The progress log shows recurring bugs in centipawn loss calculation (sessions 04 and 09) and frontend state issues — exactly the kind of thing tests prevent.

**Recommendation:** Add a `tests/` directory with pytest-based unit and integration tests.

**Suggested test coverage:**
- `engine.py`: `classify_move()` thresholds, `calculate_accuracy()` edge cases, `analyze()` with known FEN positions, `evaluate_move()` eval loss sign correctness for both colors
- `coach.py`: `_get_system_prompt()` content block structure, prompt caching markers present, system prompt changes with/without book content and board context
- `lesson.py`: `extract_lesson_json()` with valid JSON, malformed JSON, markdown-wrapped JSON, missing marker
- `patterns.py`: `detect_hanging_pieces()`, `detect_knight_fork()`, `detect_pin()`, `detect_back_rank()` with known positions, `_get_phase()` boundary values
- `main.py`: API endpoint integration tests (health check, analyze with valid/invalid FEN, chat without API key returns 503)

**Estimated scope:** ~10-15 test functions covering the most critical paths.

---

## Priority 2: API Cost Protection

**Problem:** The app requires an Anthropic API key. If hosted publicly with the server's key, any visitor consumes API tokens. The book content alone is ~57K tokens per session. This is a real financial risk.

**Options (pick one or combine):**

1. **Bring-your-own-key (BYOK):** User enters their own Anthropic API key in the frontend UI. Key is stored in the browser (localStorage or sessionStorage) and sent with each request. Backend uses the provided key instead of its own. Pros: zero cost to you, users get full experience. Cons: barrier to entry, most visitors won't have a key.

2. **Demo mode + BYOK hybrid:** Stockfish-only features (analysis, play vs coach, batch analysis) work without any API key. Chat coaching requires a user-provided key. Pros: visitors can still explore most features for free. Cons: the most impressive feature (Claude coaching) is gated.

3. **Server key with hard budget cap:** Use your own key but enforce strict rate limiting — per-IP daily token budget, global daily spend cap, request throttling. Pros: frictionless visitor experience. Cons: you pay, and it needs monitoring.

**Recommendation:** Option 2 (demo mode + BYOK) gives the best balance. Most of the impressive engineering (Stockfish analysis, batch patterns, play mode) works without Claude. The chat coaching is a bonus for visitors who have a key.

---

## Priority 3: Dockerization

**Problem:** The app requires Python 3.10+, Stockfish installed at `/usr/games/stockfish`, a virtual environment, and specific pip packages. This is too many manual steps for anyone cloning the repo, and it's required for deployment to any container hosting platform.

**Recommendation:** Add a `Dockerfile` and `docker-compose.yml` at the project root.

**Dockerfile should:**
- Use a Python 3.12 slim base image
- Install Stockfish via apt
- Copy backend source and install pip dependencies
- Serve the frontend as static files via FastAPI (add `StaticFiles` mount)
- Expose port 8000
- Use a non-root user

**docker-compose.yml should:**
- Define the single service
- Map port 8000
- Accept `ANTHROPIC_API_KEY` as an environment variable (optional)
- Include a health check

**Bonus:** This also enables one-command local setup: `docker compose up`.

---

## Priority 4: Split the Frontend

**Problem:** `chessboard.html` is 2900 lines with all CSS, JavaScript, and HTML in one file. This reads as prototypey to reviewers and makes the code harder to navigate.

**Recommendation:** Split into three files with no framework adoption:
- `index.html` — markup only, with `<link>` and `<script>` tags
- `styles.css` — all CSS extracted
- `app.js` — all JavaScript extracted

**Additional consideration:** The JavaScript has natural module boundaries that could be further separated later (board management, chat, game state, API calls), but a single `app.js` is a fine first step.

**Serving:** With the Docker setup from Priority 3, mount `src/frontend/` as a FastAPI `StaticFiles` directory. This also eliminates the need for the user to manually open an HTML file — everything is served from one origin, solving CORS in production.

---

## Priority 5: Production Deployment

**Problem:** Currently runs only on localhost. Needs HTTPS, a real domain (or subdomain), and locked-down CORS for production.

**Recommendation:**

1. **Hosting platform:** A small VPS (DigitalOcean droplet, Fly.io, or Railway) that can run Docker. Stockfish needs to run as a subprocess, which rules out serverless platforms.

2. **HTTPS:** Use a reverse proxy (Caddy is simplest — automatic HTTPS with Let's Encrypt) or the platform's built-in SSL.

3. **CORS:** Change `allow_origins=["*"]` to the actual domain once deployed.

4. **Environment:** API key via environment variable (already supported via `.env`), not committed to the repo.

---

## Out of Scope (Future Enhancements, Not Blockers)

These are things that would improve the product but are not required for a solid resume-ready deployment:

- **Lesson execution workflow** — stepping through generated lesson plans interactively
- **Multi-turn tool calling** — sending `tool_result` back to Claude for richer coaching loops
- **Streaming chat responses** — reduces perceived latency for coaching messages
- **Game import from Chess.com API** — fetch games directly instead of copy-pasting PGN
- **Mobile responsiveness** — the fixed 500px board and multi-column layout won't work on phones
- **Additional books** — more coaching material beyond Capablanca's Chess Fundamentals
- **Model upgrade** — `claude-sonnet-4-20250514` could be updated to a newer version
