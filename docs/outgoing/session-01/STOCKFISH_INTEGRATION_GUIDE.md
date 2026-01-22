# Stockfish Integration Guide

**Purpose:** Guide for integrating Stockfish chess engine with the Python backend
**Target Session:** Session 02
**Difficulty:** Intermediate

---

## Overview

Stockfish is already installed on the system (`stockfish` command available). This guide explains how to integrate it with a Python backend to provide position analysis for the Chess Coach.

---

## Architecture

```
Browser (chessboard.html)
    ↓ HTTP Request (FEN string)
Python Backend (Flask/FastAPI)
    ↓ UCI Commands via subprocess
Stockfish Engine
    ↓ Analysis Results
Python Backend
    ↓ HTTP Response (JSON)
Browser (display evaluation)
```

---

## Stockfish Basics

### UCI Protocol
Stockfish communicates via the Universal Chess Interface (UCI) protocol using stdin/stdout.

### Basic UCI Commands
```
uci                 # Initialize engine, get info
isready             # Check if engine is ready
position fen [FEN]  # Set position
go depth [N]        # Analyze to depth N
go movetime [MS]    # Analyze for N milliseconds
quit                # Shutdown engine
```

### Sample Interaction
```
> uci
< uciok

> position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
> go depth 15

< info depth 1 score cp 25 ...
< info depth 2 score cp 30 ...
< bestmove e2e4 ponder e7e5
```

---

## Python Implementation

### Option 1: Using `python-chess` Library (Recommended)

**Install:**
```bash
pip install python-chess
```

**Basic Usage:**
```python
import chess
import chess.engine

# Initialize engine
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")

# Set up position
board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

# Analyze position
info = engine.analyse(board, chess.engine.Limit(depth=15))

print(f"Evaluation: {info['score']}")
print(f"Best move: {info['pv'][0]}")

# Clean up
engine.quit()
```

**Advantages:**
- Handles UCI protocol automatically
- Robust error handling
- Actively maintained
- Great documentation

---

### Option 2: Direct Subprocess (More Control)

```python
import subprocess
import re

class StockfishEngine:
    def __init__(self, path="/usr/games/stockfish"):
        self.process = subprocess.Popen(
            path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        self._send_command("uci")
        self._wait_for("uciok")

    def _send_command(self, command):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def _wait_for(self, text):
        while True:
            line = self.process.stdout.readline().strip()
            if text in line:
                return line

    def analyze(self, fen, depth=15):
        self._send_command(f"position fen {fen}")
        self._send_command(f"go depth {depth}")

        best_move = None
        evaluation = None

        while True:
            line = self.process.stdout.readline().strip()

            # Parse evaluation
            if "score cp" in line:
                match = re.search(r"score cp (-?\d+)", line)
                if match:
                    evaluation = int(match.group(1)) / 100.0  # Convert centipawns

            # Parse best move
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break

        return {
            "evaluation": evaluation,
            "best_move": best_move
        }

    def quit(self):
        self._send_command("quit")
        self.process.wait()

# Usage
engine = StockfishEngine()
result = engine.analyze("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(result)
engine.quit()
```

---

## Backend API Design

### Flask Example

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize Stockfish (keep it running)
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")

@app.route('/api/analyze', methods=['POST'])
def analyze_position():
    data = request.get_json()
    fen = data.get('fen')

    if not fen:
        return jsonify({'error': 'FEN required'}), 400

    try:
        # Parse FEN
        board = chess.Board(fen)

        # Analyze
        info = engine.analyse(board, chess.engine.Limit(depth=15))

        # Extract data
        score = info['score'].relative
        best_move = str(info['pv'][0]) if info['pv'] else None

        return jsonify({
            'fen': fen,
            'evaluation': {
                'type': 'cp' if score.score() else 'mate',
                'value': score.score() / 100 if score.score() else score.mate()
            },
            'best_move': best_move,
            'depth': 15
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'engine': 'stockfish'})

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        engine.quit()
```

---

### FastAPI Example (Async)

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import chess.engine

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engine
engine = None

@app.on_event("startup")
async def startup_event():
    global engine
    engine = await chess.engine.popen_uci("/usr/games/stockfish")

@app.on_event("shutdown")
async def shutdown_event():
    await engine.quit()

class AnalysisRequest(BaseModel):
    fen: str
    depth: int = 15

class AnalysisResponse(BaseModel):
    fen: str
    evaluation: dict
    best_move: str
    depth: int

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_position(request: AnalysisRequest):
    try:
        board = chess.Board(request.fen)
        info = await engine.analyse(
            board,
            chess.engine.Limit(depth=request.depth)
        )

        score = info['score'].relative
        best_move = str(info['pv'][0]) if info['pv'] else None

        return {
            'fen': request.fen,
            'evaluation': {
                'type': 'cp' if score.score() else 'mate',
                'value': score.score() / 100 if score.score() else score.mate()
            },
            'best_move': best_move,
            'depth': request.depth
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "engine": "stockfish"}

# Run with: uvicorn main:app --reload
```

---

## Frontend Integration

### JavaScript Fetch Example

```javascript
async function analyzePosition(fen) {
    try {
        const response = await fetch('http://localhost:5000/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ fen: fen })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Analysis failed:', error);
        return null;
    }
}

// Usage in chessboard.html
async function analyzeCurrentPosition() {
    const fen = document.getElementById('fenDisplay').textContent;
    const analysis = await analyzePosition(fen);

    if (analysis) {
        console.log(`Evaluation: ${analysis.evaluation.value}`);
        console.log(`Best move: ${analysis.best_move}`);

        // Display on page
        document.getElementById('evaluation').textContent =
            `${analysis.evaluation.value > 0 ? '+' : ''}${analysis.evaluation.value}`;
    }
}
```

---

## Understanding Stockfish Output

### Centipawn (cp) Score
- **Positive:** White is better
- **Negative:** Black is better
- **Scale:** 100 cp = 1 pawn advantage

**Examples:**
- `cp 25` = White is up 0.25 pawns (slight advantage)
- `cp -150` = Black is up 1.5 pawns (significant advantage)
- `cp 0` = Equal position

### Mate Score
- `mate 3` = Checkmate in 3 moves
- `mate -5` = Getting checkmated in 5 moves

### Principal Variation (PV)
The best line of play according to the engine.

```
pv: e2e4 e7e5 g1f3 b8c6 f1b5
Means: 1. e4 e5 2. Nf3 Nc6 3. Bb5 (Ruy Lopez)
```

---

## Testing Checklist

### Manual Tests

1. **Engine Startup**
   ```bash
   stockfish
   # Should enter UCI mode
   ```

2. **Basic Analysis**
   ```python
   import chess.engine
   engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
   board = chess.Board()
   info = engine.analyse(board, chess.engine.Limit(depth=15))
   print(info['score'])
   engine.quit()
   ```

3. **API Endpoint**
   ```bash
   # Start server
   python app.py

   # Test endpoint
   curl -X POST http://localhost:5000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'
   ```

4. **Frontend Integration**
   - Open chessboard.html
   - Open browser console
   - Run: `analyzePosition(document.getElementById('fenDisplay').textContent)`
   - Verify analysis returns

---

## Common Issues and Solutions

### Issue 1: Stockfish Not Found
```
Error: No such file or directory: 'stockfish'
```

**Solution:**
```bash
# Find Stockfish location
which stockfish

# Use full path
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
```

---

### Issue 2: CORS Errors
```
Access to fetch at 'http://localhost:5000/api/analyze' from origin 'null'
has been blocked by CORS policy
```

**Solution (Flask):**
```python
from flask_cors import CORS
CORS(app)
```

**Solution (FastAPI):**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

---

### Issue 3: Engine Hangs
If the engine stops responding:

```python
# Set timeout on analysis
info = engine.analyse(
    board,
    chess.engine.Limit(depth=15, time=5.0)  # Max 5 seconds
)
```

---

### Issue 4: Move Format Confusion
Stockfish returns moves in long algebraic notation (e.g., "e2e4"), not SAN (e.g., "e4").

**Convert using chess.py:**
```python
board = chess.Board()
move = chess.Move.from_uci("e2e4")
san = board.san(move)  # Returns "e4"
```

---

## Performance Considerations

### Analysis Depth
- **Depth 10:** Very fast, good for quick analysis (~0.1s)
- **Depth 15:** Balanced, recommended for coaching (~1-2s)
- **Depth 20:** Strong, for deep analysis (~5-10s)
- **Depth 25+:** Very strong, slow (~30s+)

### Time Limits
```python
# Limit by depth
chess.engine.Limit(depth=15)

# Limit by time
chess.engine.Limit(time=2.0)  # 2 seconds

# Limit by nodes
chess.engine.Limit(nodes=1000000)  # 1M nodes

# Combine limits
chess.engine.Limit(depth=20, time=5.0)  # Whichever comes first
```

### Engine Reuse
- ✅ Keep engine running between requests (faster)
- ❌ Don't create new engine for each analysis (slow)

```python
# GOOD: Reuse engine
engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
for fen in positions:
    result = engine.analyse(chess.Board(fen), limit)
engine.quit()

# BAD: Create engine each time
for fen in positions:
    engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
    result = engine.analyse(chess.Board(fen), limit)
    engine.quit()
```

---

## Next Steps for Session 02

1. **Choose Framework:** Flask (simpler) or FastAPI (async, modern)
2. **Install Dependencies:**
   ```bash
   pip install python-chess flask flask-cors
   # OR
   pip install python-chess fastapi uvicorn
   ```

3. **Create Backend Structure:**
   ```
   src/backend/
   ├── app.py              # Main Flask/FastAPI app
   ├── engine.py           # Stockfish wrapper
   ├── routes/
   │   └── analyze.py      # Analysis endpoints
   └── requirements.txt
   ```

4. **Implement Features:**
   - [x] Health check endpoint
   - [x] Position analysis endpoint
   - [ ] Move suggestion endpoint
   - [ ] Game analysis endpoint (analyze all moves)

5. **Test End-to-End:**
   - Browser → API → Stockfish → API → Browser
   - Verify evaluation displays correctly
   - Test with various positions

---

## Resources

- **python-chess Documentation:** https://python-chess.readthedocs.io/
- **UCI Protocol Spec:** http://wbec-ridderkerk.nl/html/UCIProtocol.html
- **Stockfish Wiki:** https://github.com/official-stockfish/Stockfish/wiki
- **Flask Documentation:** https://flask.palletsprojects.com/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## Sample Positions for Testing

```python
TEST_POSITIONS = {
    "starting": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "equal_endgame": "8/5k2/8/8/8/8/5K2/8 w - - 0 1",
    "mate_in_one": "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
    "complex_middlegame": "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 9"
}
```

---

*This guide is meant to be used in Session 02 when building the Python backend.*
