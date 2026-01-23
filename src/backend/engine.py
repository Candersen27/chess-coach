"""
Stockfish chess engine wrapper for analysis.
"""

import chess
import chess.engine
import chess.pgn
import io
from typing import Dict, Any, Optional, Tuple, List
import asyncio


class ChessEngine:
    """Wrapper class for Stockfish chess engine."""

    def __init__(self, engine_path: str = "/usr/games/stockfish"):
        """Initialize the chess engine wrapper.

        Args:
            engine_path: Path to the Stockfish binary
        """
        self.engine_path = engine_path
        self.transport: Optional[asyncio.SubprocessTransport] = None
        self.engine: Optional[chess.engine.UciProtocol] = None

    async def start(self):
        """Start the Stockfish engine."""
        if self.engine is None:
            # popen_uci returns a tuple of (transport, protocol)
            self.transport, self.engine = await chess.engine.popen_uci(self.engine_path)

    async def stop(self):
        """Stop the Stockfish engine."""
        if self.engine is not None:
            await self.engine.quit()
            self.engine = None

    async def analyze(self, fen: str, depth: int = 15) -> Dict[str, Any]:
        """Analyze a chess position.

        Args:
            fen: FEN string representing the position
            depth: Search depth (default: 15)

        Returns:
            Dictionary containing:
                - evaluation: {"type": "cp"|"mate", "value": float|int}
                - best_move: UCI format (e.g., "e2e4")
                - best_move_san: Standard algebraic notation (e.g., "e4")
                - depth: Search depth used

        Raises:
            ValueError: If FEN is invalid
            RuntimeError: If engine is not started
        """
        if self.engine is None:
            raise RuntimeError("Engine not started. Call start() first.")

        try:
            # Parse FEN and create board
            board = chess.Board(fen)
        except ValueError as e:
            raise ValueError(f"Invalid FEN: {str(e)}")

        # Analyze position
        info = await self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth)
        )

        # Extract score from White's perspective (standard convention)
        # Positive = White is better, Negative = Black is better
        score = info['score'].white()

        # Determine evaluation type and value
        if score.is_mate():
            eval_type = "mate"
            eval_value = score.mate()
        else:
            eval_type = "cp"
            # Convert centipawns to pawns (divide by 100)
            eval_value = score.score() / 100.0

        # Extract best move
        best_move_uci = None
        best_move_san = None

        if info.get('pv') and len(info['pv']) > 0:
            best_move_uci = str(info['pv'][0])
            # Convert UCI to SAN
            best_move_san = board.san(info['pv'][0])

        return {
            "evaluation": {
                "type": eval_type,
                "value": eval_value
            },
            "best_move": best_move_uci,
            "best_move_san": best_move_san,
            "depth": depth
        }

    async def get_move(self, fen: str, elo: int = 1500) -> Dict[str, Any]:
        """Get engine's move at specified ELO level.

        Args:
            fen: FEN string representing the position
            elo: Target ELO strength (1350-2800, default: 1500)

        Returns:
            Dictionary containing:
                - move: UCI format (e.g., "e7e5")
                - move_san: Standard algebraic notation (e.g., "e5")
                - fen_after: FEN string after move is applied

        Raises:
            ValueError: If FEN is invalid or game is over
            RuntimeError: If engine is not started
        """
        if self.engine is None:
            raise RuntimeError("Engine not started. Call start() first.")

        # Clamp ELO to valid range (1350-2800 for this Stockfish version)
        elo = max(1350, min(2800, elo))

        try:
            # Parse FEN and create board
            board = chess.Board(fen)
        except ValueError as e:
            raise ValueError(f"Invalid FEN: {str(e)}")

        # Check if game is already over
        if board.is_game_over():
            raise ValueError("Game is already over (checkmate, stalemate, or insufficient material)")

        # Configure engine strength
        await self.engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": elo
        })

        # Get engine's move (1 second time limit)
        result = await self.engine.play(
            board,
            chess.engine.Limit(time=1.0)
        )

        # Apply move to board to get FEN after move
        move_uci = result.move.uci()
        move_san = board.san(result.move)
        board.push(result.move)
        fen_after = board.fen()

        return {
            "move": move_uci,
            "move_san": move_san,
            "fen_after": fen_after
        }

    async def analyze_game(self, pgn: str, depth: int = 15) -> Dict[str, Any]:
        """Analyze all moves in a PGN game.

        Args:
            pgn: PGN string of the game to analyze
            depth: Analysis depth (default: 15)

        Returns:
            Dictionary containing:
                - moves: List of move analysis dictionaries
                - summary: Game summary with accuracy and mistake counts

        Raises:
            ValueError: If PGN is invalid
            RuntimeError: If engine is not started
        """
        if self.engine is None:
            raise RuntimeError("Engine not started. Call start() first.")

        # Parse PGN
        try:
            pgn_io = io.StringIO(pgn)
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                raise ValueError("Invalid PGN: Could not parse game")
        except Exception as e:
            raise ValueError(f"Invalid PGN: {str(e)}")

        # Initialize analysis storage
        moves_analysis = []
        white_cp_losses = []
        black_cp_losses = []
        white_counts = {"blunder": 0, "mistake": 0, "inaccuracy": 0}
        black_counts = {"blunder": 0, "mistake": 0, "inaccuracy": 0}
        critical_moments = []

        # Start from the beginning
        board = game.board()
        node = game
        move_number = 1
        half_move_count = 0

        # Iterate through all moves
        for move_node in game.mainline():
            half_move_count += 1
            fen_before = board.fen()
            move = move_node.move
            color = "white" if board.turn == chess.WHITE else "black"

            # Get evaluation before the move
            try:
                eval_before_result = await self.analyze(fen_before, depth)
                eval_before_dict = eval_before_result["evaluation"]
                best_move_uci = eval_before_result["best_move"]
                best_move_san = eval_before_result["best_move_san"]

                # Convert evaluation to centipawns from current player's perspective
                if eval_before_dict["type"] == "mate":
                    # Mate scores: use large values
                    mate_value = eval_before_dict["value"]
                    if mate_value > 0:
                        eval_before_cp = 10000 if board.turn == chess.WHITE else -10000
                    else:
                        eval_before_cp = -10000 if board.turn == chess.WHITE else 10000
                else:
                    # Regular centipawn evaluation (already in pawns, convert to cp)
                    eval_before_cp = eval_before_dict["value"] * 100

            except Exception as e:
                # If analysis fails, skip this move
                board.push(move)
                continue

            # Apply the move
            move_uci = move.uci()
            move_san = board.san(move)
            board.push(move)
            fen_after = board.fen()

            # Get evaluation after the move
            try:
                eval_after_result = await self.analyze(fen_after, depth)
                eval_after_dict = eval_after_result["evaluation"]

                # Convert evaluation to centipawns
                if eval_after_dict["type"] == "mate":
                    mate_value = eval_after_dict["value"]
                    if mate_value > 0:
                        eval_after_cp = 10000 if board.turn == chess.BLACK else -10000
                    else:
                        eval_after_cp = -10000 if board.turn == chess.BLACK else 10000
                else:
                    eval_after_cp = eval_after_dict["value"] * 100

            except Exception as e:
                continue

            # Calculate centipawn loss from the moving player's perspective
            # For white: eval_before should be from white's view, eval_after should be negated
            # For black: eval_before should be negated, eval_after should be from white's view
            if color == "white":
                cp_loss = eval_before_cp - (-eval_after_cp)
            else:
                cp_loss = (-eval_before_cp) - eval_after_cp

            # Classify the move
            classification = classify_move(cp_loss)

            # Track statistics
            if color == "white":
                white_cp_losses.append(max(0, cp_loss))
                if classification == "blunder":
                    white_counts["blunder"] += 1
                    critical_moments.append(move_number if color == "white" else move_number - 1)
                elif classification == "mistake":
                    white_counts["mistake"] += 1
                elif classification == "inaccuracy":
                    white_counts["inaccuracy"] += 1
            else:
                black_cp_losses.append(max(0, cp_loss))
                if classification == "blunder":
                    black_counts["blunder"] += 1
                    critical_moments.append(move_number)
                elif classification == "mistake":
                    black_counts["mistake"] += 1
                elif classification == "inaccuracy":
                    black_counts["inaccuracy"] += 1

            # Store move analysis
            moves_analysis.append({
                "move_number": move_number,
                "color": color,
                "move_san": move_san,
                "move_uci": move_uci,
                "fen_before": fen_before,
                "fen_after": fen_after,
                "eval_before": round(eval_before_dict["value"], 2),
                "eval_after": round(eval_after_dict["value"], 2),
                "eval_change": round(-cp_loss / 100, 2),  # Convert back to pawns, negate for display
                "best_move_san": best_move_san,
                "best_move_uci": best_move_uci,
                "classification": classification
            })

            # Increment move number after black's move
            if color == "black":
                move_number += 1

        # Calculate accuracies
        white_accuracy = calculate_accuracy(white_cp_losses)
        black_accuracy = calculate_accuracy(black_cp_losses)

        # Build summary
        summary = {
            "total_moves": len(moves_analysis),
            "white_accuracy": white_accuracy,
            "black_accuracy": black_accuracy,
            "white_blunders": white_counts["blunder"],
            "white_mistakes": white_counts["mistake"],
            "white_inaccuracies": white_counts["inaccuracy"],
            "black_blunders": black_counts["blunder"],
            "black_mistakes": black_counts["mistake"],
            "black_inaccuracies": black_counts["inaccuracy"],
            "critical_moments": critical_moments[:5]  # Top 5 critical moments
        }

        return {
            "moves": moves_analysis,
            "summary": summary
        }


def classify_move(cp_loss: float) -> str:
    """Classify move based on centipawn loss.

    Args:
        cp_loss: Centipawn loss (positive value)

    Returns:
        Classification string: "excellent", "good", "inaccuracy", "mistake", or "blunder"
    """
    if cp_loss <= 0:
        return "excellent"
    elif cp_loss <= 20:
        return "good"
    elif cp_loss <= 50:
        return "inaccuracy"
    elif cp_loss <= 100:
        return "mistake"
    else:
        return "blunder"


def calculate_accuracy(cp_losses: List[float]) -> float:
    """Calculate accuracy percentage from list of centipawn losses.

    Args:
        cp_losses: List of centipawn losses (should be non-negative)

    Returns:
        Accuracy percentage (0-100)
    """
    if not cp_losses:
        return 100.0

    avg_loss = sum(abs(loss) for loss in cp_losses) / len(cp_losses)
    accuracy = max(0, min(100, 100 - (avg_loss / 2)))
    return round(accuracy, 1)
