# Session 08 Phase 1: Board Control - Documentation Package

## Overview

This directory contains all planning and specification documents for implementing board control in the AI Chess Coach. This is **Phase 1** of a two-phase feature that enables Claude to control the chessboard during coaching conversations.

## What You're Building

Enable Claude to:
- Show chess positions on the board during conversations
- Demonstrate tactics, strategies, and patterns visually
- Create an interactive "shared whiteboard" for coaching

Enable users to:
- See positions Claude is discussing (not just text)
- Make moves on Claude-shown positions
- Get coaching feedback with Stockfish accuracy
- Switch between analyzing their games and exploring positions with Claude

## Document Guide

### 1. Start Here: [SESSION_SCOPE.md](SESSION_SCOPE.md)

**Read this first** to understand:
- What we're building and why
- Success criteria
- What's in scope (and explicitly out of scope)
- High-level architecture

**Time:** 5-10 minutes

### 2. Then: [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)

**Read this second** to understand:
- Why we chose this approach
- What alternatives we rejected
- Context behind technical choices
- Lessons from previous sessions

**Time:** 10-15 minutes

### 3. Before Coding: [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)

**Read this before writing code** to understand:
- Exact API contracts
- Data structures
- Tool definitions
- Integration points
- Code patterns to follow

**Time:** 15-20 minutes

### 4. During Implementation: [IMPLEMENTATION_TASKS.md](IMPLEMENTATION_TASKS.md)

**Use this as your checklist** while coding:
- Step-by-step tasks
- Testing procedures
- Edge cases
- Troubleshooting guide

**Time:** Reference throughout implementation

## Quick Start

If you're ready to jump in:

1. ✅ Read SESSION_SCOPE.md (understand the goal)
2. ✅ Skim DESIGN_DECISIONS.md (understand the why)
3. ✅ Read TECHNICAL_SPEC.md thoroughly (understand the how)
4. ✅ Start working through IMPLEMENTATION_TASKS.md
5. ✅ Test as you go (don't save testing for the end)

## Key Concepts

### Tool Calling

Claude has a tool: `set_board_position(fen, annotation, moves)`

When Claude wants to show a position, it calls this tool. The backend parses the tool call and returns structured data to the frontend.

### Coach Demo Mode

Two modes:
- **My Game:** User's uploaded game (view-only)
- **Coach Demo:** Claude's positions (interactive)

Users can switch between them. State is preserved.

### PGN with FEN Headers

Mid-game positions use PGN with FEN headers:
```
[FEN "rnbqkb1r/pp2pppp/..."]
```

This tells chess.js where to start. Solves the "position from middle of game" problem.

### Stockfish + Claude

User makes move → Stockfish analyzes → Claude coaches with data

Same pattern as existing game analysis, just applied real-time.

## Implementation Order

Follow this sequence (detailed in IMPLEMENTATION_TASKS.md):

**Phase 1: Backend (Tasks 1-5)**
1. Update Stockfish engine methods
2. Add tool definition to coach
3. Implement tool calling
4. Add coach move endpoint
5. Update chat endpoint

**Phase 2: Frontend (Tasks 6-10)**
6. Add mode toggle UI
7. Implement state management
8. Add PGN generation
9. Update chat handler
10. Implement interactive moves

**Phase 3: Testing (Tasks 11-12)**
11. End-to-end testing
12. Edge case testing

**Phase 4: Documentation (Tasks 13-14)**
13. Update project docs
14. Code cleanup

## Testing Strategy

**Test as you build:**
- Backend: Manual API tests with curl/Postman
- Each function: Console logs and simple tests
- Frontend: Browser testing after each feature
- Integration: Full user scenarios at the end

**Don't wait until everything is done to test!**

## What Success Looks Like

You'll know Phase 1 is complete when:

✅ User asks "Show me this position" → board updates
✅ User makes moves in Coach Demo → Claude responds intelligently
✅ Mode switching works smoothly
✅ Navigation (← →) works in both modes
✅ No crashes or critical bugs

**The real test:** Can you analyze your own chess games and have Claude demonstrate alternatives on the board in a way that helps you learn?

## Common Pitfalls to Avoid

1. **Don't try to add Phase 2 features** - Stick to scope
2. **Don't skip testing** - Test each piece as you build
3. **Don't optimize prematurely** - Get it working first
4. **Don't ignore edge cases** - Check error handling
5. **Don't forget documentation** - Update project docs

## Files You'll Modify

### Backend
- `src/backend/engine.py` - Add coaching context methods
- `src/backend/coach.py` - Add tool calling
- `src/backend/main.py` - Add `/api/coach/move` endpoint

### Frontend
- `src/frontend/chessboard.html` - Everything frontend

### No New Files Required
All changes are additions/modifications to existing files.

## Time Estimate

**Total:** 2-3 hours of focused implementation

**Breakdown:**
- Backend (Tasks 1-5): 45-60 minutes
- Frontend (Tasks 6-10): 60-90 minutes
- Testing (Tasks 11-12): 30-45 minutes
- Documentation (Tasks 13-14): 15-30 minutes

These are estimates for focused work. Take breaks as needed.

## Dependencies

**No new dependencies needed!**

All required libraries are already in the project:
- python-chess ✓
- Stockfish ✓
- chessboard.js ✓
- chess.js ✓
- Claude API (anthropic) ✓

## Getting Help

If you get stuck:

1. **Check IMPLEMENTATION_TASKS.md** - Has troubleshooting section
2. **Review TECHNICAL_SPEC.md** - Has complete code examples
3. **Check existing code** - Play vs Coach has similar patterns
4. **Console logs** - Add them liberally for debugging
5. **Test incrementally** - Find where it breaks

## What Comes After

**Phase 2** (future session) will add:
- Arrow & highlight annotations on the board
- Move sequences (not just single positions)
- Lesson navigation UI
- Claude adaptive Stockfish queries

But that's for later. Focus on Phase 1 now.

## Final Checklist Before You Start

- [ ] Read SESSION_SCOPE.md completely
- [ ] Understand DESIGN_DECISIONS.md context
- [ ] Review TECHNICAL_SPEC.md thoroughly
- [ ] Have IMPLEMENTATION_TASKS.md open for reference
- [ ] Backend is running (can test `/api/chat`)
- [ ] Frontend loads without errors
- [ ] Ready to commit code incrementally

---

## Let's Build!

You have everything you need:
- Clear scope
- Detailed specs
- Step-by-step tasks
- Context on decisions

Start with Task 1 in IMPLEMENTATION_TASKS.md and work through them in order. Test as you go. You've got this!

---

*Session 08 Phase 1 Documentation - Prepared February 11, 2026*
