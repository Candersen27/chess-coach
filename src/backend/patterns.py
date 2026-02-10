"""
Pattern detection module for multi-game analysis.
Analyzes batches of games to detect recurring tactical weaknesses
and phase-specific performance patterns.
"""

import chess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TacticalPattern(Enum):
    HANGING_PIECE = "hanging_piece"
    KNIGHT_FORK = "knight_fork"
    PIN = "pin"
    BACK_RANK = "back_rank"
    DISCOVERED_ATTACK = "discovered_attack"
    SKEWER = "skewer"


class GamePhase(Enum):
    OPENING = "opening"       # Moves 1-15
    MIDDLEGAME = "middlegame"  # Moves 16-40
    ENDGAME = "endgame"       # Moves 41+


PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 100.0,
}

PIECE_NAMES = {
    chess.PAWN: "pawn",
    chess.KNIGHT: "knight",
    chess.BISHOP: "bishop",
    chess.ROOK: "rook",
    chess.QUEEN: "queen",
    chess.KING: "king",
}


def _get_phase(move_number: int) -> GamePhase:
    if move_number <= 15:
        return GamePhase.OPENING
    elif move_number <= 40:
        return GamePhase.MIDDLEGAME
    else:
        return GamePhase.ENDGAME


def _sq(square: chess.Square) -> str:
    return chess.square_name(square)


# --- Tactical pattern detectors ---
# Each takes a board position (after the blunder) and the victim's color.
# Returns (description, material_value) or None.

def detect_hanging_pieces(board: chess.Board, victim_color: chess.Color) -> Optional[Tuple[str, float]]:
    """Check if victim has undefended pieces that are attacked."""
    hanging = []
    attacker_color = not victim_color

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != victim_color or piece.piece_type == chess.KING:
            continue

        if board.attackers(attacker_color, square) and not board.attackers(victim_color, square):
            hanging.append((square, piece, PIECE_VALUES.get(piece.piece_type, 0)))

    if not hanging:
        return None

    # Report highest-value hanging piece
    hanging.sort(key=lambda x: x[2], reverse=True)
    sq, piece, value = hanging[0]
    name = PIECE_NAMES[piece.piece_type]
    return (f"{name.capitalize()} on {_sq(sq)} left undefended", value)


def detect_knight_fork(board: chess.Board, exploiter_color: chess.Color) -> Optional[Tuple[str, float]]:
    """Check if exploiter can fork valuable pieces with a knight.

    Checks both existing knight positions and one-move knight destinations.
    """
    victim_color = not exploiter_color
    best_fork = None
    best_total_value = 0
    valuable_types = (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP)

    def _check_fork_from(sq: chess.Square, b: chess.Board) -> Optional[Tuple[str, float]]:
        """Check if a knight on sq forks valuable victim pieces."""
        attacked = []
        for target_sq in b.attacks(sq):
            target = b.piece_at(target_sq)
            if target and target.color == victim_color and target.piece_type in valuable_types:
                attacked.append((target_sq, target))
        if len(attacked) >= 2:
            total = sum(PIECE_VALUES.get(p.piece_type, 0) for _, p in attacked)
            # Material at risk = the lesser piece (opponent can save only one)
            at_risk = min(PIECE_VALUES.get(p.piece_type, 0) for _, p in attacked)
            pieces_desc = " and ".join(
                PIECE_NAMES[p.piece_type] for _, p in attacked
            )
            return (f"Knight on {_sq(sq)} forks {pieces_desc}", at_risk), total
        return None, 0

    # Check existing knight positions
    for knight_sq in board.pieces(chess.KNIGHT, exploiter_color):
        result, total = _check_fork_from(knight_sq, board)
        if result and total > best_total_value:
            best_fork = result
            best_total_value = total

    # Check one-move knight destinations
    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.KNIGHT or piece.color != exploiter_color:
            continue
        test_board = board.copy()
        test_board.push(move)
        result, total = _check_fork_from(move.to_square, test_board)
        if result and total > best_total_value:
            best_fork = result
            best_total_value = total

    return best_fork


def detect_pin(board: chess.Board, victim_color: chess.Color) -> Optional[Tuple[str, float]]:
    """Check if victim has pieces pinned to their king."""
    king_sq = board.king(victim_color)
    if king_sq is None:
        return None

    best_pin = None
    best_value = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != victim_color or piece.piece_type == chess.KING:
            continue

        if not board.is_pinned(victim_color, square):
            continue

        value = PIECE_VALUES.get(piece.piece_type, 0)
        if value <= best_value:
            continue

        best_value = value
        name = PIECE_NAMES[piece.piece_type]

        # Find the pinning piece
        pin_mask = board.pin(victim_color, square)
        pinner_name = "piece"
        for candidate in chess.SQUARES:
            if candidate in (square, king_sq):
                continue
            if pin_mask & chess.BB_SQUARES[candidate]:
                cp = board.piece_at(candidate)
                if cp and cp.color != victim_color:
                    pinner_name = PIECE_NAMES[cp.piece_type]
                    break

        best_pin = (
            f"{name.capitalize()} on {_sq(square)} pinned to king by {pinner_name}",
            value,
        )

    return best_pin


def detect_back_rank(board: chess.Board, victim_color: chess.Color) -> Optional[Tuple[str, float]]:
    """Check if victim's king is vulnerable to back rank mate."""
    king_sq = board.king(victim_color)
    if king_sq is None:
        return None

    back_rank = 0 if victim_color == chess.WHITE else 7
    if chess.square_rank(king_sq) != back_rank:
        return None

    # Check if escape squares (one rank forward) are all blocked
    forward_rank = 1 if victim_color == chess.WHITE else 6
    king_file = chess.square_file(king_sq)
    attacker_color = not victim_color

    for f in range(max(0, king_file - 1), min(8, king_file + 2)):
        escape_sq = chess.square(f, forward_rank)
        occupant = board.piece_at(escape_sq)
        # If square is empty or occupied by opponent piece, and not attacked → escape exists
        if occupant is None or occupant.color != victim_color:
            if not board.is_attacked_by(attacker_color, escape_sq):
                return None
        # Own piece blocks escape

    # King is trapped; check opponent has heavy piece to exploit
    if board.pieces(chess.ROOK, attacker_color) or board.pieces(chess.QUEEN, attacker_color):
        return ("Back rank weakness - king trapped by own pawns", 100.0)

    return None


# Detection priority order (most common first)
TACTICAL_DETECTORS = [
    (TacticalPattern.HANGING_PIECE, lambda b, vc, ec: detect_hanging_pieces(b, vc)),
    (TacticalPattern.KNIGHT_FORK, lambda b, vc, ec: detect_knight_fork(b, ec)),
    (TacticalPattern.PIN, lambda b, vc, ec: detect_pin(b, vc)),
    (TacticalPattern.BACK_RANK, lambda b, vc, ec: detect_back_rank(b, vc)),
]


class PatternDetector:
    """Detects recurring patterns across multiple analyzed games."""

    def analyze_games(
        self,
        analyzed_games: List[Dict],
        player_colors: Optional[List[Optional[str]]] = None,
    ) -> Dict[str, Any]:
        """Main entry point.

        Args:
            analyzed_games: List of dicts from engine.analyze_game(),
                each with 'moves' and 'summary' keys.
            player_colors: Optional list parallel to analyzed_games.
                Each entry is 'white', 'black', or None (analyze both).

        Returns:
            Pattern summary dict (JSON-serializable).
        """
        if player_colors is None:
            player_colors = [None] * len(analyzed_games)

        patterns = self._detect_tactical_patterns(analyzed_games, player_colors)
        phases = self._analyze_phase_performance(analyzed_games, player_colors)
        recommendations = self._generate_recommendations(patterns, phases)
        overall_accuracy = self._calculate_overall_accuracy(analyzed_games, player_colors)

        return {
            "total_games": len(analyzed_games),
            "tactical_patterns": patterns,
            "phase_stats": phases,
            "overall_accuracy": overall_accuracy,
            "recommendations": recommendations,
        }

    def _detect_tactical_patterns(
        self, games: List[Dict], player_colors: List[Optional[str]]
    ) -> Dict[str, List[Dict]]:
        """Scan blunders/mistakes for tactical motifs."""
        patterns: Dict[str, List[Dict]] = {}

        for game_idx, game in enumerate(games):
            user_color = player_colors[game_idx]
            for move_data in game.get("moves", []):
                if move_data.get("classification") not in ("blunder", "mistake"):
                    continue

                # Skip opponent's moves if we know the user's color
                if user_color and move_data.get("color") != user_color:
                    continue

                fen_after = move_data.get("fen_after")
                if not fen_after:
                    continue

                try:
                    board = chess.Board(fen_after)
                except Exception:
                    continue

                color = move_data.get("color", "white")
                victim_color = chess.WHITE if color == "white" else chess.BLACK
                exploiter_color = not victim_color
                move_number = move_data.get("move_number", 0)

                # Material lost (eval_change is in pawns, negative = bad)
                eval_change = move_data.get("eval_change", 0) or 0
                lost_material = round(abs(eval_change), 1)

                # Try each detector in priority order; first match wins
                for pattern_type, detector_fn in TACTICAL_DETECTORS:
                    result = detector_fn(board, victim_color, exploiter_color)
                    if result:
                        desc, mat_value = result
                        key = pattern_type.value
                        if key not in patterns:
                            patterns[key] = []
                        patterns[key].append({
                            "game_index": game_idx,
                            "move_number": move_number,
                            "pattern": key,
                            "lost_material": lost_material if lost_material > 0 else mat_value,
                            "fen": fen_after,
                            "description": desc,
                        })
                        break  # One pattern per blunder

        return patterns

    def _analyze_phase_performance(
        self, games: List[Dict], player_colors: List[Optional[str]]
    ) -> Dict[str, Dict]:
        """Calculate accuracy and error rates by game phase."""
        phase_data = {
            phase.value: {"cp_losses": [], "blunders": 0, "mistakes": 0, "moves": 0}
            for phase in GamePhase
        }

        for game_idx, game in enumerate(games):
            user_color = player_colors[game_idx]
            for move_data in game.get("moves", []):
                # Skip opponent's moves if we know the user's color
                if user_color and move_data.get("color") != user_color:
                    continue

                move_number = move_data.get("move_number", 0)
                phase_key = _get_phase(move_number).value

                phase_data[phase_key]["moves"] += 1

                classification = move_data.get("classification", "")
                if classification == "blunder":
                    phase_data[phase_key]["blunders"] += 1
                elif classification == "mistake":
                    phase_data[phase_key]["mistakes"] += 1

                # eval_change is in pawns, negative = lost evaluation
                eval_change = move_data.get("eval_change", 0) or 0
                cp_loss = max(0, -eval_change * 100)
                phase_data[phase_key]["cp_losses"].append(cp_loss)

        result = {}
        for phase_key, data in phase_data.items():
            if data["moves"] == 0:
                continue
            cp_losses = data["cp_losses"]
            if cp_losses:
                avg_loss = sum(cp_losses) / len(cp_losses)
                accuracy = max(0.0, min(100.0, 100 - (avg_loss / 2)))
            else:
                accuracy = 100.0

            result[phase_key] = {
                "phase": phase_key,
                "avg_accuracy": round(accuracy, 1),
                "blunder_count": data["blunders"],
                "mistake_count": data["mistakes"],
                "move_count": data["moves"],
            }

        return result

    def _generate_recommendations(
        self,
        patterns: Dict[str, List[Dict]],
        phases: Dict[str, Dict],
    ) -> List[str]:
        """Generate top 3 actionable recommendations."""
        recs: List[str] = []

        # Tactical patterns sorted by frequency
        sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)

        # Rec 1: Most frequent tactical pattern (if 2+ instances)
        if sorted_patterns and len(sorted_patterns[0][1]) >= 2:
            name, instances = sorted_patterns[0]
            readable = name.replace("_", " ")
            game_count = len(set(i["game_index"] for i in instances))
            avg_loss = sum(i["lost_material"] for i in instances) / len(instances)
            recs.append(
                f"You're losing material to {readable}s "
                f"({game_count} game{'s' if game_count != 1 else ''}, "
                f"avg {avg_loss:.1f} pawns lost). "
                f"Practice recognizing {readable} patterns."
            )

        # Rec 2: Weakest phase vs strongest
        if len(phases) >= 2:
            weakest = min(phases.items(), key=lambda x: x[1]["avg_accuracy"])
            strongest = max(phases.items(), key=lambda x: x[1]["avg_accuracy"])
            gap = strongest[1]["avg_accuracy"] - weakest[1]["avg_accuracy"]

            if gap > 5 or weakest[1]["blunder_count"] >= 2:
                recs.append(
                    f"Your {weakest[0]} accuracy is low "
                    f"({weakest[1]['avg_accuracy']:.0f}% vs "
                    f"{strongest[1]['avg_accuracy']:.0f}% in {strongest[0]}). "
                    f"Focus on {weakest[0]} technique."
                )

        # Rec 3: Second most frequent pattern
        if len(sorted_patterns) >= 2 and len(sorted_patterns[1][1]) >= 1:
            name, instances = sorted_patterns[1]
            readable = name.replace("_", " ")
            game_count = len(set(i["game_index"] for i in instances))
            recs.append(
                f"Practice recognizing {readable}s "
                f"({game_count} game{'s' if game_count != 1 else ''})."
            )

        # Fallback: blunder-heavy phases
        if not recs and phases:
            for phase_key, stats in sorted(phases.items(), key=lambda x: x[1]["avg_accuracy"]):
                if stats["blunder_count"] > 0:
                    recs.append(
                        f"You had {stats['blunder_count']} blunder"
                        f"{'s' if stats['blunder_count'] != 1 else ''} "
                        f"in the {phase_key}. Review these critical moments."
                    )
                if len(recs) >= 3:
                    break

        if not recs:
            recs.append("Keep playing and analyzing more games to build a clearer pattern profile.")

        return recs[:3]

    def _calculate_overall_accuracy(
        self, games: List[Dict], player_colors: List[Optional[str]]
    ) -> float:
        """Average accuracy across all analyzed games (user's color only when known)."""
        accuracies = []
        for game_idx, game in enumerate(games):
            summary = game.get("summary", {})
            user_color = player_colors[game_idx]

            if user_color == "white":
                val = summary.get("white_accuracy")
                if val is not None:
                    accuracies.append(val)
            elif user_color == "black":
                val = summary.get("black_accuracy")
                if val is not None:
                    accuracies.append(val)
            else:
                # Unknown color — average both sides
                for key in ("white_accuracy", "black_accuracy"):
                    val = summary.get(key)
                    if val is not None:
                        accuracies.append(val)

        if not accuracies:
            return 0.0
        return round(sum(accuracies) / len(accuracies), 1)
