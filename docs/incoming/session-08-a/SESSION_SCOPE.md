# Session 08 Phase 1: Board Control Foundation

## Mission

Enable Claude to control the chessboard during coaching conversations, creating a "shared whiteboard" for visual chess instruction.

## Core User Story

```
User: [Analyzing their game] "Show me the critical moment where I went wrong"
Claude: [Loads that position on the board] "Here - move 23. Your rook is hanging."
User: [Tries a different move on the board]
Claude: [Evaluates move with Stockfish] "Good idea! But Black has Bxf7+. Let me show you."
       [Loads resulting position]
User: [Navigates back with ← button] "What should I have played?"
Claude: "Nf6 was stronger. Here's why..." [Loads Nf6 position]
```

## Deliverables

### Must Have (Session 08 Phase 1)

1. **Tool Calling Infrastructure**
   - Claude API configured with `set_board_position` tool
   - Backend parses tool calls and extracts FEN/annotation
   - Response format includes both text and board control data

2. **Coach Demo Mode**
   - Toggle between "My Game" and "Coach Demo" modes
   - "My Game": View-only, shows user's uploaded PGN
   - "Coach Demo": Interactive, shows Claude's demonstrations
   - State preservation when switching modes

3. **Board Control from Claude**
   - Claude can load any position via FEN
   - Board updates when Claude demonstrates positions
   - Annotations display alongside board
   - Works with existing ← → navigation

4. **Interactive Exploration**
   - User can make moves in Coach Demo mode
   - Backend queries Stockfish for position evaluation
   - Claude receives Stockfish context (eval + top moves)
   - Claude responds to user's move attempts

5. **PGN with Custom Starting Positions**
   - Generate PGN with `[FEN "..."]` header tag
   - chess.js correctly loads positions mid-game
   - Navigation works through Claude's demonstrated sequences

### Nice to Have (Stretch Goals)

- "Coach is thinking..." loading indicator
- Smooth board animation on position changes
- Keyboard shortcuts (space = next, backspace = prev)

### Explicitly Out of Scope (Phase 2/Later)

- ❌ Arrow & highlight annotations (Future session)
- ❌ Move sequences in single tool call (Phase 1 = single positions only)
- ❌ Structured lesson navigation UI
- ❌ Claude adaptive Stockfish queries
- ❌ Variation trees (backtracking clears forward moves)
- ❌ Progress tracking

## Success Criteria

✅ User can ask Claude to show a position → board updates
✅ User can make moves in Coach Demo mode → Claude responds
✅ User can switch between their game and coach demonstrations
✅ Navigation (← →) works for both modes
✅ Claude's coaching includes Stockfish tactical accuracy

**The real test:** Can you have a natural coaching conversation where Claude demonstrates positions and responds to your exploration?

## Technical Constraints

- **Stateless backend** - No database yet, all state in frontend
- **Reuse existing code** - Leverage Play vs Coach patterns
- **Tool calling** - Use Anthropic's function calling, not custom parsing
- **Single board** - One board that updates, no side-by-side views

## Files to Modify

### Frontend
- `src/frontend/chessboard.html` - Add mode toggle, handle tool calls, interactive moves in Coach Demo

### Backend
- `src/backend/coach.py` - Add tool definition, parse tool calls
- `src/backend/main.py` - New endpoint: `/api/coach/move`
- `src/backend/engine.py` - Expose `get_coaching_context()` and `evaluate_move()` methods

### New Files
- None (all modifications to existing files)

## Dependencies

- **Existing:** python-chess, Stockfish, chessboard.js, chess.js, Claude API
- **No new dependencies required**

## Estimated Complexity

**Medium** - Reuses existing patterns (Play vs Coach, tool calling), but requires coordination between multiple components.

**Time estimate:** 2-3 hours of focused implementation + testing

## Phased Approach

**This is Phase 1 of a two-phase Session 08:**

- **Phase 1 (This session):** Basic board control with single positions
- **Phase 2 (Future):** Arrow annotations, enhanced interactivity, lesson navigation

Focus on getting the foundation solid. Phase 2 features are explicitly out of scope.

---

*Prepared for Claude Code implementation - February 11, 2026*
