# Backend Implementation Tasks

## Task 1: Create Pattern Detection Module

**File:** `src/backend/patterns.py`

### PatternDetector Class

```python
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class TacticalPattern(Enum):
    HANGING_PIECE = "hanging_piece"
    KNIGHT_FORK = "knight_fork"
    PIN = "pin"
    DISCOVERED_ATTACK = "discovered_attack"
    BACK_RANK = "back_rank"
    SKEWER = "skewer"

class GamePhase(Enum):
    OPENING = "opening"      # Moves 1-15
    MIDDLEGAME = "middlegame"  # Moves 15-40
    ENDGAME = "endgame"      # Moves 40+

@dataclass
class TacticalInstance:
    """Single instance of a tactical pattern"""
    game_index: int
    move_number: int
    pattern: TacticalPattern
    lost_material: float  # In pawns (e.g., 3.0 for minor piece)
    fen: str
    description: str

@dataclass
class PhaseStats:
    """Statistics for a game phase"""
    phase: GamePhase
    avg_accuracy: float
    blunder_count: int
    mistake_count: int
    move_count: int

@dataclass
class PatternSummary:
    """Aggregated pattern analysis across games"""
    total_games: int
    tactical_patterns: Dict[TacticalPattern, List[TacticalInstance]]
    phase_stats: Dict[GamePhase, PhaseStats]
    overall_accuracy: float
    recommendations: List[str]  # Top 3 recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        pass

class PatternDetector:
    def __init__(self):
        pass
    
    def analyze_games(self, analyzed_games: List[Dict]) -> PatternSummary:
        """
        Main entry point. Takes list of analyzed games from /api/game/analyze
        and returns aggregated pattern summary.
        
        Args:
            analyzed_games: List of dicts from existing game analysis endpoint
                Each dict has: pgn, moves (with classifications), accuracy, etc.
        
        Returns:
            PatternSummary with all detected patterns and recommendations
        """
        patterns = self._detect_tactical_patterns(analyzed_games)
        phases = self._analyze_phase_performance(analyzed_games)
        recommendations = self._generate_recommendations(patterns, phases)
        
        return PatternSummary(
            total_games=len(analyzed_games),
            tactical_patterns=patterns,
            phase_stats=phases,
            overall_accuracy=self._calculate_overall_accuracy(analyzed_games),
            recommendations=recommendations
        )
    
    def _detect_tactical_patterns(self, games: List[Dict]) -> Dict[TacticalPattern, List[TacticalInstance]]:
        """
        Analyze blunders/mistakes to identify tactical themes.
        
        Logic:
        - For each blunder/mistake, examine the position (FEN)
        - Check for common tactical patterns:
          - Hanging piece: piece attacked, not defended
          - Knight fork: knight attacks 2+ valuable pieces
          - Pin: piece can't move without exposing more valuable piece
          - Back rank: king on back rank with no escape squares
        
        Use python-chess to analyze positions.
        """
        pass
    
    def _analyze_phase_performance(self, games: List[Dict]) -> Dict[GamePhase, PhaseStats]:
        """
        Calculate accuracy and error rates by game phase.
        
        Opening: moves 1-15
        Middlegame: moves 15-40
        Endgame: moves 40+
        """
        pass
    
    def _generate_recommendations(self, 
                                  patterns: Dict[TacticalPattern, List[TacticalInstance]],
                                  phases: Dict[GamePhase, PhaseStats]) -> List[str]:
        """
        Generate top 3 recommendations based on pattern frequency.
        
        Priority:
        1. Most frequent tactical pattern (if appears in 3+ games)
        2. Weakest phase (lowest accuracy with 2+ blunders)
        3. Second most frequent tactical pattern OR second weakest phase
        
        Format: Human-readable strings
        Example: "You're losing material to knight forks (4 games, avg 3.2 pawns lost)"
        """
        pass
    
    def _calculate_overall_accuracy(self, games: List[Dict]) -> float:
        """Average accuracy across all games"""
        pass
```

### Pattern Detection Logic Hints

**For Tactical Patterns:**
```python
import chess

def is_hanging_piece(board: chess.Board, move: chess.Move) -> bool:
    """Check if move leaves a piece hanging"""
    # Make move
    # Check if any of our pieces are attacked and not defended
    # Revert move
    pass

def is_knight_fork(board: chess.Board, move: chess.Move) -> bool:
    """Check if opponent's knight forks our pieces"""
    # Look for knight that attacks 2+ of our valuable pieces
    pass

# Similar functions for pin, back_rank, etc.
```

**Key libraries you already have:**
- `chess` - for position analysis
- `chess.pgn` - for parsing PGN

---

## Task 2: Create Batch Analysis Endpoint

**File:** `src/backend/main.py`

Add new route:

```python
from patterns import PatternDetector, PatternSummary

@app.post("/api/games/analyze-batch")
async def analyze_batch(request: Request):
    """
    Analyze multiple games and detect patterns.
    
    Request body:
    {
        "pgns": ["[Event ...] 1. e4 ...", "[Event ...] 1. d4 ...", ...]
    }
    
    Response:
    {
        "analyzed_games": [...],  # Full analysis of each game
        "pattern_summary": {...}   # Aggregated patterns
    }
    """
    try:
        data = await request.json()
        pgns = data.get("pgns", [])
        
        if len(pgns) < 5:
            return JSONResponse(
                status_code=400,
                content={"error": "Please provide at least 5 games for pattern analysis"}
            )
        
        # Analyze each game using existing logic
        analyzed_games = []
        for pgn_str in pgns:
            # Reuse logic from /api/game/analyze
            # Or extract to shared function
            game_analysis = await analyze_single_game(pgn_str)
            analyzed_games.append(game_analysis)
        
        # Detect patterns
        detector = PatternDetector()
        pattern_summary = detector.analyze_games(analyzed_games)
        
        return {
            "analyzed_games": analyzed_games,
            "pattern_summary": pattern_summary.to_dict()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

async def analyze_single_game(pgn_str: str) -> Dict:
    """
    Extract single game analysis logic from /api/game/analyze
    so it can be reused in batch endpoint.
    """
    # Move logic from existing /api/game/analyze here
    # Return dict with: pgn, moves, accuracy, game_info, etc.
    pass
```

**Refactoring Note:** You'll want to extract the game analysis logic from the existing `/api/game/analyze` endpoint into a reusable function that both endpoints can call.

---

## Task 3: Update Coach Context

**File:** `src/backend/coach.py`

Modify the chat endpoint to accept pattern context:

```python
async def chat(message: str, context: dict = None) -> str:
    """
    context can now include:
    {
        "analyzed_games": {...},
        "pattern_summary": {...}
    }
    """
    # Build system prompt
    system_parts = [BASE_COACHING_PROMPT, book_library.get_context()]
    
    # Add pattern context if available
    if context and "pattern_summary" in context:
        patterns = context["pattern_summary"]
        pattern_context = f"""
## Recent Game Analysis

You have analyzed {patterns['total_games']} of the student's recent games.

### Identified Weaknesses:
{format_patterns_for_claude(patterns)}

### Recommendations:
{chr(10).join(f"- {rec}" for rec in patterns['recommendations'])}

Use this data to provide personalized coaching. When the student asks for help,
reference these specific patterns and recommend targeted practice.
"""
        system_parts.append(pattern_context)
    
    # Continue with existing chat logic...
```

---

## Testing

### Test Pattern Detection

Create `tests/test_patterns.py`:

```python
import pytest
from backend.patterns import PatternDetector, TacticalPattern, GamePhase

def test_knight_fork_detection():
    """Test that knight forks are detected"""
    # Use sample game where player loses material to knight fork
    # Verify TacticalInstance is created correctly
    pass

def test_phase_analysis():
    """Test that game phases are analyzed correctly"""
    # Game with strong opening, weak endgame
    # Verify PhaseStats show this pattern
    pass

def test_recommendations():
    """Test that recommendations are generated"""
    # 5 games with 3 knight fork blunders
    # Verify "knight forks" is top recommendation
    pass
```

### Test with Real Data

Use sample games from `data/samples/`:
```bash
curl -X POST http://localhost:8000/api/games/analyze-batch \
  -H "Content-Type: application/json" \
  -d '{
    "pgns": ["...", "...", "..."]
  }'
```

Expected response structure:
```json
{
  "analyzed_games": [...],
  "pattern_summary": {
    "total_games": 5,
    "tactical_patterns": {
      "knight_fork": [
        {
          "game_index": 0,
          "move_number": 23,
          "pattern": "knight_fork",
          "lost_material": 3.0,
          "fen": "...",
          "description": "Knight on e4 forks rook and bishop"
        }
      ]
    },
    "phase_stats": {
      "opening": {
        "phase": "opening",
        "avg_accuracy": 87.5,
        "blunder_count": 0,
        "mistake_count": 1,
        "move_count": 15
      }
    },
    "overall_accuracy": 78.3,
    "recommendations": [
      "You're losing material to knight forks (3 games, avg 3.2 pawns lost)",
      "Your endgame accuracy is low (65% vs 85% in opening)",
      "Practice recognizing pinned pieces (2 games)"
    ]
  }
}
```
