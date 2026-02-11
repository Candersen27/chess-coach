# Session 08 Phase 1: Design Decisions

## Purpose of This Document

This document captures the key design decisions made during Session 08 planning. It explains **what** we decided, **why** we chose that approach, and **what alternatives** were considered. This context helps during implementation and future modifications.

---

## Decision 1: Tool Calling Protocol (Option 3 - Phased)

### What We Decided

Use Anthropic's native tool calling (function calling) for Claude to control the board, implemented in two phases:
- **Phase 1:** Basic tool calling for board control (positions only)
- **Phase 2:** Full interactive exploration (user makes moves, Claude responds)

### Why This Choice

**Advantages:**
- Most powerful and extensible approach
- Enables interactive coaching (the real value)
- Native Claude feature, well-documented
- Reuses existing Play vs Coach patterns
- Not significantly more complex than alternatives

**What we rejected:**
- **Option 1 (XML tags):** Brittle parsing, harder to extend
- **Option 2 (JSON):** Would need backend reformatting, less robust
- Going straight to full implementation: Too risky, phased approach manages complexity

### Impact on Implementation

- Add tool definition to Claude API call
- Parse `tool_use` blocks in responses
- Backend is slightly more complex but more robust
- Frontend receives structured data, easy to handle

### Future Considerations

Phase 2 will add:
- User move handling in Coach Demo
- Claude querying Stockfish adaptively
- More sophisticated board interactions

---

## Decision 2: Board State Management (Single Positions + PGN Navigation)

### What We Decided

- Show one position at a time (no sequences in Phase 1)
- Reuse existing ← → navigation buttons
- Build PGN with `[FEN]` headers for mid-game positions
- Maintain position history for navigation

### Why This Choice

**Advantages:**
- Leverages existing navigation code (no reinvention)
- PGN with FEN is standard chess notation
- chess.js already supports FEN headers
- Simple mental model: one position shown, user can navigate
- Easy to extend to sequences in Phase 2

**What we rejected:**
- **Multiple positions in one tool call:** Too complex for Phase 1
- **New navigation UI:** Unnecessary, existing buttons work
- **Multiple boards side-by-side:** Over-engineered, single board is standard

### Technical Details

```
Standard PGN: Assumes starting position
PGN with FEN: Starts from any position
[FEN "rnbqkb1r/..."] header tells chess.js where to start
```

This solves the "positions from mid-game" problem elegantly.

### Impact on Implementation

- `buildPGNFromFEN()` function creates valid PGN
- chess.js `load_pgn()` works without modification
- Navigation logic unchanged
- Position history is simple array

---

## Decision 3: Coach Demo Mode (Mode-Based Interactivity)

### What We Decided

Two distinct modes with different behaviors:
- **My Game:** View-only, shows uploaded game, analyze only
- **Coach Demo:** Interactive, shows Claude's positions, can make moves

State preserved when switching between modes.

### Why This Choice

**Advantages:**
- Clear mental model: "I'm looking at my game" vs "Coach is showing me something"
- No data loss when switching
- Natural workflow: analyze → coach demonstrates → back to analyze
- Simple implementation: mode check in `onDrop()`

**What we rejected:**
- **Always interactive:** Confusing, users might accidentally modify their game
- **Always view-only:** Defeats purpose of interactive coaching
- **Permission-based (Claude grants):** Too complex, confusing UX

### User Experience

```
User loads game → "My Game" mode (can't move pieces)
Claude shows position → Auto-switch to "Coach Demo" (can try moves)
User clicks "My Game" → Back to their game, right where they left off
```

### Impact on Implementation

- Mode toggle buttons in UI
- `gameState.activeMode` tracks current mode
- `onDrop()` checks mode before allowing moves
- Mode switch functions preserve state

---

## Decision 4: Stockfish Integration (Hybrid - Claude + Engine)

### What We Decided

Claude receives Stockfish analysis before coaching on user moves:
1. User makes move
2. Stockfish evaluates position before/after
3. Stockfish finds top alternatives
4. Claude receives this data + coaches in natural language

### Why This Choice

**Advantages:**
- Tactically accurate (Stockfish catches all tactics)
- Natural coaching (Claude explains in human terms)
- Reuses existing Stockfish integration
- Same pattern as current game analysis
- Fast enough (shallow depth ~100-200ms)

**What we rejected:**
- **Claude only:** Not reliable for tactics (~1500-1800 level)
- **Stockfish only:** Robotic, not personalized coaching
- **Always deep analysis:** Too slow for interactive use

### The Architecture

```
User move → Stockfish (eval + top moves) → Claude (coaching with data) → Response
```

This is identical to existing game analysis, just applied real-time.

### Impact on Implementation

- New engine methods: `get_coaching_context()`, `evaluate_move()`
- Backend calls Stockfish before calling Claude
- Claude prompt includes eval data
- Same move classification thresholds (excellent/good/mistake/blunder)

### Future Enhancement (Phase 2)

Claude can query Stockfish adaptively:
- "Let me analyze this deeper..." [calls analyze_position tool]
- Used for complex positions or teaching specific concepts

---

## Decision 5: Lesson Integration (Manual Triggering)

### What We Decided

When Claude generates lesson plans, first position loads manually:
- Claude creates lesson plan, shows in chat
- User confirms "let's start"
- Claude loads first position via tool call
- User asks for subsequent activities

### Why This Choice

**Advantages:**
- User-controlled pacing
- No surprise board changes
- Simple Phase 1 implementation
- Easy to extend to automatic navigation later

**What we rejected:**
- **Fully automatic:** Could be jarring, user loses control
- **Full lesson navigator UI from start:** Over-engineered for MVP
- **No integration:** Misses opportunity to use board control with lessons

### Future Enhancement

Phase 2 could add:
- Lesson state tracking
- Activity-by-activity navigation UI
- Progress indicators
- Completion tracking

---

## Decision 6: Single Board Display

### What We Decided

One board that updates to show different positions. No side-by-side views.

### Why This Choice

**Industry standard:**
- Chess.com: Single board
- Lichess: Single board
- chess24: Single board

**UX advantages:**
- Clear focus (one position at a time)
- Less cognitive load
- Natural sequential thinking
- Easier mobile support

**What we rejected:**
- **Multiple boards:** Over-engineered, unnecessary complexity
- **Split view:** Not how chess players naturally think

### How Comparisons Work

"Show me your move vs best move":
1. Show user's position
2. User navigates or asks
3. Show alternative position
4. Use ← → to compare

Sequential comparison teaches better than side-by-side.

### Future Enhancement: Arrow Annotations

Instead of multiple boards, add arrows/highlights to single board:
- Claude draws arrows showing candidate moves
- Highlights weak/strong squares
- Shows attack/defense lines
- User can also draw arrows

**This makes single board even more powerful** without multiple boards. Planned for future session.

---

## Decision 7: Navigation Reuse

### What We Decided

Reuse existing ← → navigation buttons for Coach Demo mode. Same buttons work for both My Game and Coach Demo.

### Why This Choice

**Advantages:**
- Zero new UI code needed
- Familiar to user
- Consistent experience
- Natural for chess players

**How it works:**
- My Game: Navigate through uploaded game moves
- Coach Demo: Navigate through positions Claude showed
- Same buttons, different PGN loaded

### Linear History (Phase 1)

Backtracking clears forward moves (like browser back button).

**Phase 2 could add:** Variation trees, but not needed for MVP.

---

## Decision 8: Stateless Backend (Continued)

### What We Decided

Continue with stateless backend, all game state managed in frontend.

### Why This Choice

**Context:**
- Database is Phase 3 (deliberately deferred)
- Current architecture works well
- Frontend already manages game state

**For Session 08:**
- Coach Demo state in frontend `gameState` object
- Conversation history in frontend
- Pattern analysis in frontend
- No backend state needed for board control

### When Database Becomes Necessary

Future features that need persistence:
- Lesson completion tracking
- Progress over time
- User profiles
- Performance analytics

But Phase 1 works fine without it.

---

## Decision 9: Phase 1 vs Phase 2 Scope

### Phase 1 (Session 08)

**Focus:** Get foundation working
- Basic tool calling
- Single positions
- Mode switching
- Interactive moves with Stockfish feedback

**Goal:** Prove the concept, ship working feature

### Phase 2 (Future Session)

**Additions:**
- Arrow & highlight annotations
- Move sequences in tool calls
- Lesson navigation UI
- Claude adaptive Stockfish queries
- Enhanced interactivity

**Why separate phases:**
- Manage complexity
- Ship value incrementally
- Validate approach before building more
- Iterate based on actual usage

### What This Means for Implementation

**DO in Phase 1:**
- Everything in SESSION_SCOPE.md deliverables
- Test thoroughly, get it solid

**DON'T in Phase 1:**
- Try to add "just one more feature"
- Build UI for features not in scope
- Optimize prematurely

Ship it, use it, then improve it.

---

## Decision 10: Error Handling Strategy

### What We Decided

**Graceful degradation:**
- Tool call fails → Claude text response still works
- Stockfish fails → Return error, don't crash
- Invalid move → Snapback, show error message
- API timeout → User-friendly message

**User experience:**
- Never crash the app
- Always provide feedback
- Allow retry
- Log errors for debugging

### Implementation Guidelines

```javascript
try {
    // Attempt operation
} catch (error) {
    console.error('Detail for dev:', error);
    showUserMessage('Simple explanation');
    // Allow user to continue
}
```

---

## Decision 11: Performance Considerations

### Stockfish Depth

**Phase 1:** depth=15 for coaching moves
- Fast enough (~200ms)
- Accurate enough for 1000-2000 rated players
- Can increase if needed

**Future:** Claude can request deeper analysis adaptively

### Claude Response Time

**Typical:** 1-3 seconds
- Stockfish analysis: ~200ms
- Claude API: ~1-2 seconds
- Total: Acceptable for coaching

**UX:** Show "thinking" indicator during wait

### Prompt Caching

Already implemented in Session 06:
- Book content cached
- Reduces cost and latency
- Still works with tool calling

---

## Technical Debt & Future Improvements

### Known Limitations (Phase 1)

1. **No variation trees** - Backtracking clears forward
2. **No move sequences** - One position per tool call
3. **No arrow annotations** - Text only
4. **No lesson state** - Manual progression

These are **intentional scope limits**, not bugs.

### Refactoring Opportunities

**If Phase 1 works well:**
- Extract board control logic to separate module
- Create reusable PGN builder utility
- Standardize mode switching pattern
- Consider state management library (if complexity grows)

**But don't refactor prematurely** - Ship Phase 1 first.

---

## Lessons from Previous Sessions

### What We Learned

**Session 05-06 (Chat + Books):**
- Prompt caching works great
- Tool calling is reliable
- Simple APIs are better

**Session 07 (Pattern Detection):**
- Start simple, iterate
- Real usage shows what's needed
- Documentation helps continuity

**Applied to Session 08:**
- Phased approach (don't overcommit)
- Reuse working patterns
- Focus on core value
- Document decisions for future

---

## Success Metrics

### How We'll Know Phase 1 Worked

**Technical:**
- [ ] No crashes
- [ ] All deliverables completed
- [ ] Tests pass

**User Value:**
- [ ] Creator actually uses it to analyze games
- [ ] Board control feels natural
- [ ] Interactive coaching helps learning
- [ ] Easier to understand patterns with visual aid

**The Real Test:**
Does the creator prefer this over Chess.com analysis for their own games?

---

## Conclusion

These decisions prioritize:
1. **Shipping value** - Working feature over perfect feature
2. **User experience** - Natural flow, clear mental model
3. **Technical soundness** - Reuse patterns, manage complexity
4. **Future flexibility** - Easy to extend without rewrite

Phase 1 is intentionally limited in scope. Get it working, use it, learn from it, then build Phase 2.

---

*Design decisions documented for Session 08 Phase 1 - February 11, 2026*
