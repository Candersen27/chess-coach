# Session 07: Integration Testing Guide

## End-to-End Test Flow

### Test 1: Basic Pattern Detection

**Steps:**
1. Start backend: `uvicorn main:app --reload --port 8000`
2. Open `chessboard.html` in browser
3. Click "Batch Analysis" tab
4. Paste 5-10 games from `data/samples/` (or your own games)
5. Click "Analyze Games"

**Expected Results:**
- Loading message appears
- After ~30-60 seconds, pattern summary displays
- See:
  - Total games count
  - Overall accuracy percentage
  - 1-3 recommendations
  - Tactical patterns section (may be empty if no patterns found)
  - Phase stats (opening/middlegame/endgame)

**Success Criteria:**
- No errors in console
- Backend returns 200 status
- Pattern summary displays correctly

---

### Test 2: Pattern Data in Chat Context

**Steps:**
1. After completing Test 1 (with analysis loaded)
2. Switch to "Analysis" or "Play" tab
3. Open chat panel
4. Send message: "What should I work on?"

**Expected Results:**
- Coach response references the pattern analysis
- Example: "Based on your recent games, I noticed you're struggling with knight forks..."
- Recommendations should align with pattern summary

**Success Criteria:**
- Claude receives pattern context in API call
- Response is personalized to detected patterns
- Not generic advice

---

### Test 3: Persistence

**Steps:**
1. Complete Test 1 (analyze games)
2. Refresh the page (F5)
3. Check if pattern summary reappears

**Expected Results:**
- Pattern summary automatically loads from localStorage
- All data intact (recommendations, patterns, phase stats)

**Success Criteria:**
- No need to re-analyze
- Data persists across page reloads

---

### Test 4: Export/Import

**Steps:**
1. Complete Test 1 (analyze games)
2. Click "Export Analysis" button
3. Verify JSON file downloads
4. Click "Clear" button (clears analysis)
5. Click "Import Analysis" button
6. Select the exported JSON file

**Expected Results:**
- Export: JSON file downloads with date in filename
- Clear: Summary disappears
- Import: Summary reappears with exact same data

**Success Criteria:**
- JSON file is valid and complete
- Import restores all analysis data
- No data loss

---

### Test 5: Edge Cases

**Test 5a: Too Few Games**
- Paste only 3 games
- Click "Analyze Games"
- **Expected:** Error message "Please provide at least 5 games"

**Test 5b: Invalid PGN**
- Paste garbage text
- Click "Analyze Games"
- **Expected:** Error message about invalid PGN

**Test 5c: No Patterns Found**
- Analyze 5 perfect computer games (no blunders)
- **Expected:** "No significant tactical patterns detected" message

---

## Manual Testing with Real Games

### Getting Test Data

**From Lichess:**
1. Go to https://lichess.org/@/YourUsername
2. Click on a game
3. Click "Share & export" → "Download PGN"
4. Repeat for 5-10 games
5. Paste all PGNs into batch analysis

**From Chess.com:**
1. Go to your game archive
2. Click on each game
3. Click "Download" → "PGN"
4. Combine into one textarea

### What to Look For

Your own games should reveal real patterns:
- Do recommendations make sense?
- Do you recognize the tactical mistakes?
- Is the phase analysis accurate?

**Example findings you might see:**
- "You're hanging pieces in the opening (3/10 games)" → Need to slow down
- "Endgame accuracy drops to 62%" → Need endgame practice
- "Knight forks cost you 12 pawns across 4 games" → Tactic blindness

---

## Backend Testing

### Unit Tests

Run pattern detector tests:
```bash
pytest tests/test_patterns.py -v
```

### API Testing

Test batch endpoint directly:
```bash
curl -X POST http://localhost:8000/api/games/analyze-batch \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

Where `test_data.json`:
```json
{
  "pgns": [
    "[Event \"Test Game 1\"]...",
    "[Event \"Test Game 2\"]...",
    "[Event \"Test Game 3\"]...",
    "[Event \"Test Game 4\"]...",
    "[Event \"Test Game 5\"]..."
  ]
}
```

**Expected Response Structure:**
```json
{
  "analyzed_games": [ /* 5 game analysis objects */ ],
  "pattern_summary": {
    "total_games": 5,
    "tactical_patterns": { /* ... */ },
    "phase_stats": { /* ... */ },
    "overall_accuracy": 78.5,
    "recommendations": [ /* ... */ ]
  }
}
```

---

## Performance Testing

### Timing Expectations

For 10 games with ~40 moves each:
- Stockfish analysis: ~30-60 seconds
- Pattern detection: ~2-5 seconds
- **Total:** ~1 minute

If it takes longer:
- Check Stockfish depth setting
- Verify async is working
- Profile the pattern detection code

---

## Debugging Checklist

If things don't work:

**Backend Issues:**
- [ ] Check Stockfish is running (`ps aux | grep stockfish`)
- [ ] Check FastAPI logs for errors
- [ ] Verify `/api/games/analyze-batch` route exists
- [ ] Test single game analysis works first
- [ ] Print pattern detection intermediate results

**Frontend Issues:**
- [ ] Check browser console for errors
- [ ] Verify fetch request is sent (Network tab)
- [ ] Check localStorage is enabled
- [ ] Verify JSON response is valid
- [ ] Check display functions are called

**Integration Issues:**
- [ ] Verify pattern data structure matches expectations
- [ ] Check Claude API receives pattern context
- [ ] Verify coaching prompt includes pattern section
- [ ] Test with simpler patterns first

---

## Success Criteria for Session 07

Session is complete when:

- [ ] Can analyze 5-10 games in batch
- [ ] Pattern summary displays correctly
- [ ] Recommendations are relevant
- [ ] Chat includes pattern context
- [ ] Export/import works
- [ ] localStorage persists data
- [ ] Tested with YOUR real games
- [ ] Found at least one genuine insight about your play

The final test: **Does this help you understand your weaknesses better than Chess.com analysis?**
