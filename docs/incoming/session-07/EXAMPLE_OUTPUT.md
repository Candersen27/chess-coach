# Session 07: Example Output

## Example Pattern Summary

This is what a successful analysis should look like:

### Input: 10 Recent Games

```
[Event "Rated Rapid game"]
[Site "https://lichess.org/abc123"]
[Date "2025.02.01"]
[White "Player"]
[Black "Opponent"]
[Result "0-1"]
...

[Event "Rated Rapid game"]
[Site "https://lichess.org/def456"]
...
(8 more games)
```

### Output: Pattern Summary

```json
{
  "total_games": 10,
  "overall_accuracy": 76.3,
  "tactical_patterns": {
    "knight_fork": [
      {
        "game_index": 2,
        "move_number": 18,
        "pattern": "knight_fork",
        "lost_material": 5.0,
        "fen": "r1bqkb1r/ppp2ppp/2n2n2/3pp3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq -",
        "description": "Knight on c6 forks queen on d8 and rook on a8"
      },
      {
        "game_index": 5,
        "move_number": 24,
        "pattern": "knight_fork",
        "lost_material": 3.0,
        "fen": "...",
        "description": "Knight on e5 forks king and bishop"
      },
      {
        "game_index": 7,
        "move_number": 15,
        "pattern": "knight_fork",
        "lost_material": 3.0,
        "fen": "...",
        "description": "Knight on d4 forks rook and bishop"
      }
    ],
    "hanging_piece": [
      {
        "game_index": 1,
        "move_number": 12,
        "pattern": "hanging_piece",
        "lost_material": 3.0,
        "fen": "...",
        "description": "Bishop on c4 left undefended after knight moved"
      }
    ],
    "back_rank": [
      {
        "game_index": 9,
        "move_number": 34,
        "pattern": "back_rank",
        "lost_material": 100.0,
        "fen": "...",
        "description": "Back rank mate - king trapped by own pawns"
      }
    ]
  },
  "phase_stats": {
    "opening": {
      "phase": "opening",
      "avg_accuracy": 84.2,
      "blunder_count": 1,
      "mistake_count": 3,
      "move_count": 150
    },
    "middlegame": {
      "phase": "middlegame",
      "avg_accuracy": 75.8,
      "blunder_count": 5,
      "mistake_count": 8,
      "move_count": 250
    },
    "endgame": {
      "phase": "endgame",
      "avg_accuracy": 68.4,
      "blunder_count": 3,
      "mistake_count": 4,
      "move_count": 120
    }
  },
  "recommendations": [
    "You're losing material to knight forks (3 games, average 3.7 pawns). Practice recognizing knight fork patterns.",
    "Your endgame accuracy is significantly lower (68%) than your opening (84%). Focus on endgame technique.",
    "Back rank weaknesses cost you 1 game. Always create luft for your king."
  ]
}
```

### UI Display

**Summary Stats:**
```
┌──────────────────┐  ┌──────────────────┐
│ Games Analyzed   │  │ Overall Accuracy │
│       10         │  │      76.3%       │
└──────────────────┘  └──────────────────┘
```

**Recommendations:**
```
⚠️ Top Recommendations

• You're losing material to knight forks (3 games, average 3.7 pawns). 
  Practice recognizing knight fork patterns.

• Your endgame accuracy is significantly lower (68%) than your opening (84%). 
  Focus on endgame technique.

• Back rank weaknesses cost you 1 game. Always create luft for your king.
```

**Tactical Patterns:**
```
KNIGHT FORK (3 instances)
  Game 3, Move 18: Knight on c6 forks queen on d8 and rook on a8 (Lost 5.0 pawns)
  Game 6, Move 24: Knight on e5 forks king and bishop (Lost 3.0 pawns)
  Game 8, Move 15: Knight on d4 forks rook and bishop (Lost 3.0 pawns)

HANGING PIECE (1 instance)
  Game 2, Move 12: Bishop on c4 left undefended after knight moved (Lost 3.0 pawns)

BACK RANK (1 instance)
  Game 10, Move 34: Back rank mate - king trapped by own pawns (Lost 100.0 pawns)
```

**Phase Performance:**
```
Opening       84.2%  (1 blunders, 3 mistakes)
Middlegame    75.8%  (5 blunders, 8 mistakes)
Endgame       68.4%  (3 blunders, 4 mistakes)
```

---

## Example Chat Interaction

**User:** "What should I work on?"

**Coach (with pattern context):**

"Based on analyzing your last 10 games, I can see some clear areas to focus on:

**Immediate Priority: Knight Fork Recognition**

You've lost material to knight forks in 3 different games, costing you an average of 3.7 pawns each time. This is a tactical pattern that's very learnable! Knights are tricky because they move in an L-shape that's less intuitive than bishops or rooks.

Want me to create a practice lesson focused on spotting and preventing knight forks? We can work through the specific positions from your games where this happened.

**Secondary Focus: Endgame Technique**

Your accuracy drops significantly in the endgame (68%) compared to your opening (84%). This is common - endgames require precise calculation and technique. The good news is that endgames are very studyable.

Which would you like to tackle first - the knight fork pattern or endgame fundamentals?"

---

## Example Lesson Plan Generation

**User:** "Let's work on knight forks"

**Coach generates:**

```json
{
  "title": "Knight Fork Pattern Recognition",
  "goal": "Eliminate knight fork blunders from your games",
  "activities": [
    {
      "type": "position_study",
      "description": "Review the 3 positions from your games where you were forked",
      "position_fen": "r1bqkb1r/ppp2ppp/2n2n2/3pp3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq -",
      "key_concepts": [
        "Knight on c6 attacks both queen and rook",
        "Pieces on same color squares are vulnerable to knight forks",
        "Always check knight moves before placing pieces"
      ]
    },
    {
      "type": "tactics_drill",
      "description": "15 knight fork puzzles at your level",
      "puzzle_theme": "knight_fork",
      "count": 15
    },
    {
      "type": "practice_game",
      "description": "Play a game focusing on knight fork awareness",
      "focus": "Before each move, check: Can opponent's knight fork me?"
    }
  ]
}
```

---

This is the ideal outcome for Session 07!
