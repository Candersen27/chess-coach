# Troubleshooting Guide

**Last Updated:** January 22, 2025
**Session:** 01

---

## Quick Diagnostics

### Is Everything Working?

Run these checks to verify your setup:

```bash
# 1. Verify Stockfish
stockfish
# Should enter UCI mode. Type "quit" to exit.

# 2. Check frontend files exist
ls -lh ~/projects/chess-coach/src/frontend/
# Should show: chessboard.html, CSS, JS, img folder

# 3. Verify piece images
ls ~/projects/chess-coach/src/frontend/img/chesspieces/wikipedia/
# Should show 12 PNG files (wP, wN, wB, wR, wQ, wK, bP, bN, bB, bR, bQ, bK)

# 4. Open chessboard in browser
cd ~/projects/chess-coach/src/frontend
explorer.exe chessboard.html
```

---

## Common Issues

### Issue 1: Chessboard Won't Open

**Symptoms:**
- `explorer.exe chessboard.html` does nothing
- Double-clicking file in Windows Explorer doesn't open browser

**Solutions:**

**Option A: Use Direct Windows Path**
```bash
cd ~/projects/chess-coach/src/frontend
wslpath -w $(pwd)/chessboard.html
# Copy the output (starts with \\wsl.localhost\...)
# Paste into browser address bar
```

**Option B: Copy to Windows Filesystem**
```bash
cp -r ~/projects/chess-coach /mnt/c/Users/[YourUsername]/
# Then open from C:\Users\[YourUsername]\chess-coach\src\frontend\chessboard.html
```

**Option C: Install wslu**
```bash
sudo apt update && sudo apt install -y wslu
wslview ~/projects/chess-coach/src/frontend/chessboard.html
```

---

### Issue 2: Chess Pieces Not Showing

**Symptoms:**
- Board displays but squares are empty or show broken images
- Browser console shows 404 errors for image files

**Diagnosis:**
```javascript
// In browser console:
console.log(window.location.href);
// Should be file:///... path, not http://...
```

**Solutions:**

**Solution A: Verify Images Exist**
```bash
ls -la ~/projects/chess-coach/src/frontend/img/chesspieces/wikipedia/
# Should show 12 PNG files
```

**Solution B: Re-download Images**
```bash
cd ~/projects/chess-coach/src/frontend/img/chesspieces/wikipedia
rm -f *.png
for piece in wP wN wB wR wQ wK bP bN bB bR bQ bK; do
  wget -q "https://chessboardjs.com/img/chesspieces/wikipedia/${piece}.png" -O "${piece}.png"
done
ls -la
```

**Solution C: Check pieceTheme Configuration**
```javascript
// In browser console:
// Check if piece images are loading from correct path
document.querySelectorAll('img').forEach(img => console.log(img.src));
```

If images are loading from wrong path, check [chessboard.html](../../src/frontend/chessboard.html) line 200:
```javascript
pieceTheme: 'img/chesspieces/wikipedia/{piece}.png',  // Should be relative path
```

---

### Issue 3: PGN File Won't Load

**Symptoms:**
- "Load PGN" button doesn't work
- File picker opens but file doesn't load
- Error message: "Failed to load PGN"

**Diagnosis:**
```javascript
// In browser console after attempting to load:
// Check for error messages
```

**Solutions:**

**Solution A: Check PGN Format**
Valid PGN requires headers and moves:
```
[Event "Game"]
[Site "Chess.com"]
[Date "2025.01.22"]

1. e4 e5 2. Nf3
```

Invalid PGN (missing headers):
```
1. e4 e5 2. Nf3
```

**Solution B: Test with Sample File**
```bash
cat ~/projects/chess-coach/data/samples/Chrandersen_vs_magedoooo_2025.09.29.pgn
# Should show valid PGN with headers
```

**Solution C: Manual Load via Console**
```javascript
// In browser console:
const pgn = `[Event "Test"]
[Site "Test"]
[Date "2025.01.22"]

1. e4 e5 2. Nf3`;

chessBoard.loadPGN(pgn);
```

---

### Issue 4: Navigation Buttons Disabled

**Symptoms:**
- Previous/Next buttons are grayed out
- Clicking buttons does nothing
- Keyboard shortcuts don't work

**Diagnosis:**
```javascript
// In browser console:
console.log(document.getElementById('moveNumber').textContent);
// Should show something like "5 / 48" if game is loaded
```

**Solutions:**

**Solution A: Load a Game First**
The navigation buttons only work after loading a PGN or making moves.
1. Click "Load PGN"
2. Select a PGN file
3. Buttons should enable

**Solution B: Check Move History**
```javascript
// In browser console:
// This accesses internal state (not part of public API)
console.log('Has moves:', document.getElementById('moveNumber').textContent !== '-');
```

**Solution C: Reset Board**
```javascript
// In browser console:
chessBoard.resetBoard();
chessBoard.makeMove("e2", "e4");
chessBoard.makeMove("e7", "e5");
// Now navigation should work
```

---

### Issue 5: Drag and Drop Not Working

**Symptoms:**
- Can't drag pieces
- Pieces snap back to original position
- No piece movement at all

**Diagnosis:**
```javascript
// In browser console:
console.log('jQuery loaded:', typeof jQuery !== 'undefined');
console.log('Chessboard loaded:', typeof Chessboard !== 'undefined');
console.log('Chess.js loaded:', typeof Chess !== 'undefined');
```

**Solutions:**

**Solution A: Check Browser Console for Errors**
Open Developer Tools (F12) and check Console tab for errors.

**Solution B: Viewing Historical Position**
Drag-drop is intentionally disabled when viewing past positions.
- Click "End" button to go to current position
- Now you should be able to drag pieces

**Solution C: Check Turn**
You can only move pieces for the side to move.
```javascript
// In browser console:
const fen = document.getElementById('fenDisplay').textContent;
console.log('Side to move:', fen.split(' ')[1]); // 'w' or 'b'
```

**Solution D: Reload Page**
```
Ctrl + R (or F5)
```

If still not working, try hard refresh:
```
Ctrl + Shift + R (or Ctrl + F5)
```

---

### Issue 6: JavaScript API Not Working

**Symptoms:**
- `chessBoard.setPosition()` returns error
- Functions not defined
- "chessBoard is not defined"

**Diagnosis:**
```javascript
// In browser console:
typeof chessBoard
// Should return 'object', not 'undefined'
```

**Solutions:**

**Solution A: Wait for Page Load**
API is only available after page fully loads. Open console AFTER page loads.

**Solution B: Check Function Name**
```javascript
// Correct:
chessBoard.setPosition("start");

// Incorrect:
chessboard.setPosition("start");  // Note: lowercase 'b'
Chessboard.setPosition("start");  // Different object
```

**Solution C: Verify Page Loaded Correctly**
```javascript
// In console:
Object.keys(chessBoard);
// Should show: ['init', 'setPosition', 'makeMove', 'loadPGN', ...]
```

---

### Issue 7: Stockfish Not Found (Future Session)

**Symptoms:**
- Error: "No such file or directory: 'stockfish'"
- Backend can't connect to engine

**Diagnosis:**
```bash
which stockfish
# Should return: /usr/games/stockfish
```

**Solutions:**

**Solution A: Verify Installation**
```bash
stockfish
# Should start engine. Type "quit" to exit.
```

**Solution B: Install Stockfish**
```bash
sudo apt update
sudo apt install -y stockfish
```

**Solution C: Use Full Path**
In your Python code:
```python
# Instead of:
engine = chess.engine.SimpleEngine.popen_uci("stockfish")

# Use:
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
```

---

### Issue 8: CORS Errors (Future Session)

**Symptoms:**
- "blocked by CORS policy"
- Frontend can't connect to backend
- Network errors in console

**Diagnosis:**
```javascript
// In browser console, try:
fetch('http://localhost:5000/api/health')
  .then(r => r.json())
  .then(d => console.log(d))
  .catch(e => console.error(e));
```

**Solutions:**

**Solution A: Enable CORS in Flask**
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable for all routes
```

**Solution B: Enable CORS in FastAPI**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solution C: Test Backend Directly**
```bash
# Test with curl instead of browser
curl http://localhost:5000/api/health
```

---

## Browser Compatibility

### Tested Browsers ✅
- Chrome 90+
- Firefox 88+
- Edge 90+

### Known Issues ⚠️
- **IE 11:** Not supported (uses ES6+ JavaScript)
- **Safari < 14:** May have issues with modern JavaScript features

### Recommended
Use latest Chrome, Firefox, or Edge for best experience.

---

## Performance Issues

### Slow PGN Loading

**Symptom:** Loading large PGN files (100+ moves) takes several seconds

**Solution:**
This is normal for very large games. For better performance:
- Split large PGN files into separate games
- Consider lazy loading (future enhancement)

---

### Memory Usage High

**Symptom:** Browser using 500MB+ RAM

**Cause:** Normal for web applications with interactive graphics

**Solution:**
- Close other browser tabs
- Restart browser periodically
- Modern browsers handle this well

---

## Data Issues

### Sample PGN File Missing

**Symptom:** Can't find sample game file

**Solution:**
```bash
# Check if file exists
ls ~/projects/chess-coach/data/samples/

# If missing, you need a PGN file
# Download from Chess.com:
# 1. Go to chess.com/games/archive
# 2. Click on a game
# 3. Download PGN
# 4. Save to ~/projects/chess-coach/data/samples/
```

---

### Move Notation Looks Wrong

**Symptom:** Moves show as "e2e4" instead of "e4"

**Issue:** Using UCI format instead of SAN format

**Solution:**
The board uses SAN (Standard Algebraic Notation) for display. If you see UCI format:
```javascript
// Convert UCI to SAN (future feature)
const board = new Chess();
const move = board.move('e2e4');
console.log(move.san); // "e4"
```

---

## Debugging Tools

### Browser Developer Tools

**Open Console:**
- Chrome/Edge: `Ctrl + Shift + J` or F12 → Console
- Firefox: `Ctrl + Shift + K` or F12 → Console

**Useful Commands:**
```javascript
// Check what's loaded
console.log('jQuery:', typeof jQuery);
console.log('Chess:', typeof Chess);
console.log('Chessboard:', typeof Chessboard);
console.log('chessBoard API:', typeof chessBoard);

// Get current state
console.log('FEN:', document.getElementById('fenDisplay').textContent);
console.log('Move:', document.getElementById('moveNumber').textContent);

// Test API
chessBoard.setPosition("start");
chessBoard.makeMove("e2", "e4");
chessBoard.goToStart();
```

---

### Network Tab (Future)

For debugging API calls:
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "XHR" or "Fetch"
4. Make API call
5. Inspect request/response

---

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Check browser console for errors
3. Try in a different browser
4. Try reloading the page (Ctrl + Shift + R)

### Information to Provide

When reporting issues, include:
- **Browser:** Chrome 120, Firefox 115, etc.
- **OS:** Windows 11, WSL Ubuntu 22.04, etc.
- **Error Message:** Exact text from console
- **Steps to Reproduce:** What you did before the error
- **Expected vs Actual:** What should happen vs what happens

### Useful Commands for Diagnostics

```bash
# System info
uname -a
lsb_release -a

# Check files
ls -lR ~/projects/chess-coach/src/frontend/

# Check Stockfish
stockfish
# Type "quit" to exit

# Check Python (future sessions)
python3 --version
pip list | grep chess
```

---

## Reset Everything

If all else fails, start fresh:

```bash
# Backup first (if you made changes)
cp -r ~/projects/chess-coach ~/projects/chess-coach.backup

# Re-download frontend files
cd ~/projects/chess-coach/src/frontend

# Re-download chessboard.js
wget -q https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css
wget -q https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js

# Re-download piece images
mkdir -p img/chesspieces/wikipedia
cd img/chesspieces/wikipedia
for piece in wP wN wB wR wQ wK bP bN bB bR bQ bK; do
  wget -q "https://chessboardjs.com/img/chesspieces/wikipedia/${piece}.png" -O "${piece}.png"
done

# Verify
ls -la
```

Then reload the page in your browser.

---

## Known Limitations (Not Bugs)

### Current Version
1. **Promotion:** Always promotes to queen (no piece selection UI)
2. **Animation:** Pieces jump instantly (no smooth animation)
3. **Highlighting:** Last move not highlighted
4. **Arrows:** Can't draw arrows on board
5. **Analysis:** No position evaluation yet (coming in Session 02)
6. **Offline:** Requires internet for jQuery and chess.js CDN

These are intentional simplifications for Phase 1.

---

## Future Session Issues

### Session 02: Backend Setup

**Potential Issues:**
- Port 5000 already in use → Change port or kill process
- Python version < 3.8 → Upgrade Python
- pip install fails → Check internet, try with sudo
- Virtual environment issues → Recreate venv

**Solutions:** See STOCKFISH_INTEGRATION_GUIDE.md

---

### Session 04: Database Setup

**Potential Issues:**
- PostgreSQL not installed → `sudo apt install postgresql`
- Can't connect to DB → Check pg_hba.conf permissions
- Migration errors → Drop and recreate DB

**Solutions:** TBD in Session 04 documentation

---

## Emergency Contacts

- **Project Documentation:** `~/projects/chess-coach/docs/`
- **Session Summaries:** `~/projects/chess-coach/docs/outgoing/session-XX/`
- **Source Code:** `~/projects/chess-coach/src/`

---

*If you encounter an issue not listed here, document it for future reference!*
