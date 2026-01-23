"""
Stockfish chess engine wrapper for analysis.
"""

import chess
import chess.engine
from typing import Dict, Any, Optional, Tuple
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

        # Extract score (relative to side to move)
        score = info['score'].relative

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
