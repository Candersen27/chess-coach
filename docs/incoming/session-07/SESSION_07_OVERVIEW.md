# Session 07: Multi-Game Pattern Detection

**Date:** February 10, 2025
**Goal:** Enable batch game analysis with pattern detection and data-driven coaching recommendations

## What We're Building

Transform the coach from reactive to proactive by analyzing multiple games and identifying recurring weaknesses.

### User Flow

```
1. User pastes 5-10 PGNs into "Batch Analysis" tab
2. Backend analyzes all games with Stockfish
3. PatternDetector aggregates findings across games
4. Frontend displays pattern summary
5. Pattern data included in Claude's context
6. Coach provides data-driven recommendations
7. User can export/import analysis as JSON
```

## Core Components

### Backend (Python/FastAPI)
- `src/backend/patterns.py` - NEW: Pattern detection logic
- `src/backend/main.py` - NEW ROUTE: `/api/games/analyze-batch`
- `src/backend/coach.py` - MODIFY: Accept pattern context in chat

### Frontend (HTML/JS)
- `src/frontend/chessboard.html` - MODIFY: Add Batch Analysis tab
- State management for analyzed games
- localStorage persistence
- Export/import functionality

## Success Criteria

- [ ] Can analyze 5-10 games in one request
- [ ] Identifies tactical patterns (forks, pins, hanging pieces, back rank)
- [ ] Identifies phase weaknesses (opening/middlegame/endgame)
- [ ] Displays top 3 recommendations
- [ ] Pattern data passed to Claude for coaching
- [ ] Analysis persists in localStorage
- [ ] Can export/import analysis as JSON

## Key Decisions (Already Made)

- **Storage:** Session-level persistence (localStorage + export)
- **Minimum games:** 5 for meaningful patterns
- **Pattern categories:** Tactical motifs + phase weaknesses (MVP scope)
- **UI:** Paste multiple PGNs in textarea
- **State:** Frontend manages analyzed games (matches existing architecture)

## Implementation Order

1. Backend pattern detection
2. Batch analysis endpoint
3. Frontend UI additions
4. State management & persistence
5. AI context integration
6. Testing with real games

---

*Estimated time: 2-3 hours*
