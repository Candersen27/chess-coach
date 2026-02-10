# Session 05 QA Checklist

Test everything below with the backend running (`uvicorn main:app --reload --port 8000`) and `chessboard.html` open in browser.

---

## 1. Chat — Basic Functionality

- [ ] Initial greeting ("Hi! I'm your chess coach...") appears on page load
- [ ] Type a message and click Send — response appears
- [ ] Type a message and press Enter — response appears
- [ ] "Thinking..." indicator shows while waiting for response
- [ ] "Thinking..." disappears and is replaced by the actual response
- [ ] User messages appear on the right (blue)
- [ ] Coach messages appear on the left (gray)
- [ ] Send button disables while waiting, re-enables after response
- [ ] Input field clears after sending
- [ ] Input field regains focus after response arrives
- [ ] Empty message (just spaces) does NOT send

## 2. Chat — Multi-Turn Conversation

- [ ] Send 3+ messages in a row — coach remembers context from earlier messages
- [ ] Ask a follow-up question referencing something the coach said — it should respond coherently
- [ ] Have a 5+ message conversation — check that it doesn't break or slow down noticeably

## 3. Chat — Scrolling & Overflow

- [ ] Send enough messages to overflow the chat panel — it should scroll
- [ ] New messages auto-scroll to the bottom
- [ ] Can manually scroll up to read older messages
- [ ] Very long coach response wraps properly (doesn't overflow the panel)

## 4. Chat — Error Handling

- [ ] Stop the backend server, then send a message — should show "Sorry, I had trouble responding"
- [ ] Restart the backend — chat should work again on next message
- [ ] Check browser console for clean error logging (no uncaught exceptions)

## 5. Chat — Board Context

- [ ] Load a PGN file, navigate to a specific position, then ask "What do you think about this position?" — coach should reference the FEN or position details
- [ ] Start a Play vs Coach game, make a few moves, then ask about the position — mode should be "play"
- [ ] Analyze a position (click Analyze Position), then ask about it — mode should be "analysis"
- [ ] On the starting position with no moves, ask a question — board context should still be sent (starting FEN, idle mode)

## 6. Keyboard Shortcuts — No Interference

- [ ] Click into the chat input, type a message with arrow keys in the text — board should NOT navigate
- [ ] Click into the chat input, press Home/End — cursor moves in input, board stays put
- [ ] Click outside the chat input, press arrow keys — board navigation works normally
- [ ] Press Enter when chat input is NOT focused — nothing happens (no accidental send)

## 7. Existing Features — Regression Testing

These should all still work exactly as before:

### Board & Navigation
- [ ] Board renders at correct size (500x500)
- [ ] Drag and drop pieces in free play mode
- [ ] Load a PGN file — moves load correctly
- [ ] Navigate with buttons: Start, Previous, Next, End
- [ ] Navigate with keyboard: Left, Right, Home, End
- [ ] Flip Board button works
- [ ] Reset Board button works

### Position Analysis
- [ ] Click "Analyze Position" — evaluation and best move appear
- [ ] Analysis panel shows evaluation (green/red coloring)
- [ ] Analysis works on different positions (navigate to mid-game, analyze)

### Play vs Coach (Stockfish)
- [ ] Start new game as White — can make moves, coach responds
- [ ] Start new game as Black — coach moves first
- [ ] ELO selector changes difficulty
- [ ] Game over detection works (play to checkmate or stalemate)
- [ ] Can't move on opponent's turn

### Game Analysis
- [ ] Load a PGN, click "Analyze Full Game" — analysis completes
- [ ] Accuracy percentages display for both colors
- [ ] Color-coded move list appears
- [ ] Clicking a move in the list jumps to that position
- [ ] Export Plain PGN works
- [ ] Export Annotated PGN works
- [ ] Loading spinner and progress bar show during analysis

## 8. Layout & Responsiveness

- [ ] Three-column layout displays correctly (board | panels | chat)
- [ ] Chat panel is visible without horizontal scrolling on a normal monitor (1920px wide)
- [ ] Shrink browser window — layout degrades gracefully (no overlapping elements)
- [ ] All panels remain readable and usable

## 9. Rapid Fire / Stress

- [ ] Send a message, then immediately send another before the first response arrives — no crash or duplicate messages
- [ ] Click Send rapidly multiple times on empty input — nothing breaks
- [ ] Reload the page — fresh state, greeting appears, conversation history is cleared (expected behavior)

## 10. Backend Verification

- [ ] Health check: `curl http://localhost:8000/api/health` returns `{"status":"ok","engine":"stockfish"}`
- [ ] API docs accessible at `http://localhost:8000/docs` — chat endpoint is listed
- [ ] Chat endpoint shows in Swagger with correct request/response schema

---

## Bug Report Template

If something breaks, note:

| Field | Value |
|-------|-------|
| **Test item** | (which checklist item) |
| **Expected** | (what should happen) |
| **Actual** | (what actually happened) |
| **Steps to reproduce** | (exactly what you did) |
| **Console errors** | (any errors in browser dev tools console) |
| **Server logs** | (any errors in the uvicorn terminal) |
| **Screenshot** | (if visual issue) |

---

*Mark items with [x] as you test them. Report any failures using the template above.*
