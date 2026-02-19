"""
FastAPI backend for chess analysis using Stockfish.
"""

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from anthropic import RateLimitError

from engine import ChessEngine
from coach import ChessCoach
from books import BookLibrary
from patterns import PatternDetector


# Global instances
chess_engine = ChessEngine()
chess_coach = None
book_library = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifespan of the FastAPI application."""
    global chess_coach, book_library
    # Startup: Initialize the chess engine, book library, and coach
    await chess_engine.start()
    print("Chess engine started successfully")
    try:
        chess_coach = ChessCoach()
        book_library = chess_coach.library
        print("Chess coach initialized successfully")
    except ValueError as e:
        print(f"Warning: Chess coach not available - {e}")
        # Still load books even if coach API key is missing
        book_library = BookLibrary()
    yield
    # Shutdown: Clean up the chess engine
    await chess_engine.stop()
    print("Chess engine stopped")


# Create FastAPI app
app = FastAPI(
    title="Chess Coach API",
    description="Backend API for chess analysis using Stockfish",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for position analysis."""
    fen: str = Field(..., description="FEN string of the position to analyze")
    depth: int = Field(default=15, ge=1, le=30, description="Analysis depth (1-30)")


class EvaluationModel(BaseModel):
    """Evaluation model."""
    type: str = Field(..., description="Evaluation type: 'cp' (centipawns) or 'mate'")
    value: float = Field(..., description="Evaluation value in pawns or mate distance")


class AnalysisResponse(BaseModel):
    """Response model for position analysis."""
    fen: str = Field(..., description="FEN string of the analyzed position")
    evaluation: EvaluationModel = Field(..., description="Position evaluation")
    best_move: str | None = Field(None, description="Best move in UCI notation")
    best_move_san: str | None = Field(None, description="Best move in SAN notation")
    depth: int = Field(..., description="Analysis depth used")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="API status")
    engine: str = Field(..., description="Chess engine name")


class MoveRequest(BaseModel):
    """Request model for getting engine move."""
    fen: str = Field(..., description="FEN string of the current position")
    elo: int = Field(default=1500, ge=1350, le=2800, description="Engine ELO strength (1350-2800)")


class MoveResponse(BaseModel):
    """Response model for engine move."""
    move: str = Field(..., description="Move in UCI notation (e.g., 'e2e4')")
    move_san: str = Field(..., description="Move in SAN notation (e.g., 'e4')")
    fen_after: str = Field(..., description="FEN string after the move is applied")


class GameAnalysisRequest(BaseModel):
    """Request model for full game analysis."""
    pgn: str = Field(..., description="PGN string of the game to analyze")
    depth: int = Field(default=15, ge=1, le=30, description="Analysis depth (1-30)")


class MoveAnalysis(BaseModel):
    """Analysis data for a single move."""
    move_number: int = Field(..., description="Move number in the game")
    color: str = Field(..., description="Color that played the move: 'white' or 'black'")
    move_san: str = Field(..., description="Move in SAN notation (e.g., 'e4')")
    move_uci: str = Field(..., description="Move in UCI notation (e.g., 'e2e4')")
    fen_before: str = Field(..., description="FEN before the move")
    fen_after: str = Field(..., description="FEN after the move")
    eval_before: Optional[float] = Field(None, description="Evaluation before move (in pawns)")
    eval_after: Optional[float] = Field(None, description="Evaluation after move (in pawns)")
    eval_change: Optional[float] = Field(None, description="Change in evaluation")
    best_move_san: str = Field(..., description="Best move in SAN notation")
    best_move_uci: str = Field(..., description="Best move in UCI notation")
    classification: str = Field(..., description="Move quality: excellent, good, inaccuracy, mistake, or blunder")


class GameSummary(BaseModel):
    """Summary statistics for the analyzed game."""
    total_moves: int = Field(..., description="Total number of moves analyzed")
    white_accuracy: float = Field(..., description="White's accuracy percentage")
    black_accuracy: float = Field(..., description="Black's accuracy percentage")
    white_blunders: int = Field(..., description="Number of blunders by White")
    white_mistakes: int = Field(..., description="Number of mistakes by White")
    white_inaccuracies: int = Field(..., description="Number of inaccuracies by White")
    black_blunders: int = Field(..., description="Number of blunders by Black")
    black_mistakes: int = Field(..., description="Number of mistakes by Black")
    black_inaccuracies: int = Field(..., description="Number of inaccuracies by Black")
    critical_moments: List[int] = Field(..., description="Move numbers of critical moments (blunders)")


class GameAnalysisResponse(BaseModel):
    """Response model for full game analysis."""
    moves: List[MoveAnalysis] = Field(..., description="Analysis for each move")
    summary: GameSummary = Field(..., description="Game summary statistics")


class BatchAnalysisRequest(BaseModel):
    """Request model for batch game analysis."""
    pgns: List[str] = Field(..., description="List of PGN strings to analyze")
    depth: int = Field(default=15, ge=1, le=30, description="Analysis depth (1-30)")
    username: Optional[str] = Field(None, description="Player's username to filter analysis to their moves only")


class BoardContext(BaseModel):
    """Board context for chat messages."""
    fen: Optional[str] = None
    last_move: Optional[str] = None
    mode: Optional[str] = None  # "analysis", "play", "idle"
    pgn: Optional[str] = None


class ChatMessage(BaseModel):
    """A single message in conversation history."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for chat with coach."""
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    board_context: Optional[BoardContext] = None
    pattern_context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response model for chat with coach."""
    message: str
    suggested_action: Optional[dict] = None
    board_control: Optional[dict] = None
    game_action: Optional[dict] = None
    usage: Optional[dict] = None


class CoachMoveRequest(BaseModel):
    """Request model for coaching a user's move in Coach Demo mode."""
    fen: str = Field(..., description="FEN of the position BEFORE the move")
    move: str = Field(..., description="Move in Standard Algebraic Notation (e.g., 'Nf6')")
    context: dict = Field(default_factory=dict, description="Conversation context")


# Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Health status and engine information
    """
    return {
        "status": "ok",
        "engine": "stockfish"
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_position(request: AnalysisRequest):
    """Analyze a chess position.

    Args:
        request: Analysis request containing FEN and depth

    Returns:
        Analysis result with evaluation and best move

    Raises:
        HTTPException: 400 for invalid FEN, 500 for engine errors
    """
    try:
        result = await chess_engine.analyze(request.fen, request.depth)

        return {
            "fen": request.fen,
            "evaluation": result["evaluation"],
            "best_move": result["best_move"],
            "best_move_san": result["best_move_san"],
            "depth": result["depth"]
        }

    except ValueError as e:
        # Invalid FEN
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("Analysis failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/move", response_model=MoveResponse)
async def get_engine_move(request: MoveRequest):
    """Get engine's move for a position at specified ELO level.

    Args:
        request: Move request containing FEN and ELO

    Returns:
        Engine's move in UCI and SAN notation, plus resulting FEN

    Raises:
        HTTPException: 400 for invalid FEN or game over, 500 for engine errors
    """
    try:
        result = await chess_engine.get_move(request.fen, request.elo)

        return {
            "move": result["move"],
            "move_san": result["move_san"],
            "fen_after": result["fen_after"]
        }

    except ValueError as e:
        # Invalid FEN or game over
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("Move generation failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Move generation failed: {str(e)}")


@app.post("/api/game/analyze", response_model=GameAnalysisResponse)
async def analyze_game(request: GameAnalysisRequest):
    """Analyze all moves in a complete game.

    Args:
        request: Game analysis request containing PGN and depth

    Returns:
        Analysis result with move-by-move evaluations and game summary

    Raises:
        HTTPException: 400 for invalid PGN, 500 for engine errors
    """
    try:
        result = await chess_engine.analyze_game(request.pgn, request.depth)

        return {
            "moves": result["moves"],
            "summary": result["summary"]
        }

    except ValueError as e:
        # Invalid PGN
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Engine or other errors
        raise HTTPException(status_code=500, detail=f"Game analysis failed: {str(e)}")


@app.post("/api/games/analyze-batch")
async def analyze_batch(request: BatchAnalysisRequest):
    """Analyze multiple games and detect recurring patterns.

    Args:
        request: Batch analysis request with list of PGNs and depth

    Returns:
        Analyzed games and aggregated pattern summary

    Raises:
        HTTPException: 400 if fewer than 5 games, 500 for engine errors
    """
    import io
    import chess.pgn

    if len(request.pgns) < 5:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 5 games for pattern analysis",
        )

    analyzed_games = []
    player_colors = []  # 'white', 'black', or None per game
    errors = []

    for i, pgn_str in enumerate(request.pgns):
        try:
            result = await chess_engine.analyze_game(pgn_str.strip(), request.depth)
            analyzed_games.append(result)

            # Determine which color the user played in this game
            color = None
            if request.username:
                pgn_io = io.StringIO(pgn_str.strip())
                game = chess.pgn.read_game(pgn_io)
                if game:
                    white_player = game.headers.get("White", "")
                    black_player = game.headers.get("Black", "")
                    uname = request.username.lower()
                    if uname in white_player.lower():
                        color = "white"
                    elif uname in black_player.lower():
                        color = "black"
            player_colors.append(color)

        except ValueError as e:
            errors.append(f"Game {i + 1}: {str(e)}")
        except Exception as e:
            errors.append(f"Game {i + 1}: Analysis failed - {str(e)}")

    if len(analyzed_games) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(analyzed_games)} games analyzed successfully "
                   f"(need at least 5). Errors: {'; '.join(errors)}",
        )

    detector = PatternDetector()
    pattern_summary = detector.analyze_games(analyzed_games, player_colors)

    return {
        "analyzed_games": analyzed_games,
        "pattern_summary": pattern_summary,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_coach(request: ChatRequest):
    """Chat with the chess coach (with board control via tools).

    Args:
        request: Chat request with message, conversation history, and board context

    Returns:
        Coach's response with optional board_control for position display

    Raises:
        HTTPException: 503 if coach not initialized, 500 for API errors
    """
    if chess_coach is None:
        raise HTTPException(status_code=503, detail="Chess coach not available (check API key)")

    try:
        history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        board_ctx = request.board_context.model_dump() if request.board_context else None

        response = await chess_coach.chat_with_tools(
            message=request.message,
            conversation_history=history,
            board_context=board_ctx,
            pattern_context=request.pattern_context,
        )
        return response

    except RateLimitError as e:
        logger.warning("Chat rate limited: %s", str(e))
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment and try again.")

    except Exception as e:
        logger.error("Chat failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/coach/move")
async def coach_move_endpoint(request: CoachMoveRequest):
    """Handle user move in Coach Demo mode.

    Gets Stockfish analysis of the move, then asks Claude to provide
    coaching feedback with the engine data as context.

    Args:
        request: CoachMoveRequest with FEN (before move), move in SAN, and context

    Returns:
        Coaching response with optional board_control and Stockfish evaluation
    """
    if chess_coach is None:
        raise HTTPException(status_code=503, detail="Chess coach not available (check API key)")

    try:
        # Get Stockfish analysis of the move
        move_analysis = await chess_engine.evaluate_move(
            fen=request.fen,
            move_san=request.move,
            depth=15
        )

        # Build coaching prompt with Stockfish context
        best_move_info = ""
        if move_analysis["best_move"]:
            best_move_info = f"- Best move was: {move_analysis['best_move']['san']} (eval: {move_analysis['best_move']['eval']:.2f})"

        coaching_prompt = (
            f"The user just played: {request.move}\n\n"
            f"Stockfish analysis:\n"
            f"- Evaluation before: {move_analysis['eval_before']:.2f}\n"
            f"- Evaluation after: {move_analysis['eval_after']:.2f}\n"
            f"- Evaluation loss: {move_analysis['eval_loss']:.2f}\n"
            f"- Move classification: {move_analysis['classification']}\n"
            f"{best_move_info}\n\n"
            f"Current context: {request.context.get('current_demonstration', 'General coaching')}\n\n"
            f"Provide coaching feedback on this move. If it's a mistake or blunder, "
            f"use set_board_position to show the consequences or a better alternative."
        )

        # Get Claude response with tool calling (skip book — move coaching uses Stockfish data)
        response = await chess_coach.chat_with_tools(
            message=coaching_prompt,
            conversation_history=request.context.get("conversation_history", []),
            include_book=False,
        )

        return {
            "message": response["message"],
            "board_control": response.get("board_control"),
            "stockfish_eval": move_analysis,
            "status": "success"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except RateLimitError as e:
        logger.warning("Coach move rate limited: %s", str(e))
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment and try again.")

    except Exception as e:
        logger.error("Coach move failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Coach move failed: {str(e)}")


@app.get("/api/books")
async def list_books():
    """List available chess books and their structure.

    Returns:
        List of books with metadata, chapters, and topics
    """
    if book_library is None:
        return {"books": []}

    books = []
    for title, book in book_library.books.items():
        chapters = []
        for part in book["parts"]:
            for ch in part["chapters"]:
                sections = [
                    {"number": s["section_number"], "title": s["title"], "topics": s["topics"]}
                    for s in ch["sections"]
                ]
                chapters.append({
                    "number": ch["chapter_number"],
                    "title": ch["title"],
                    "sections": sections,
                })

        books.append({
            "title": title,
            "author": book["metadata"]["author"],
            "year": book["metadata"]["year"],
            "total_sections": book["metadata"]["total_sections"],
            "total_games": book["metadata"]["total_games"],
            "chapters": chapters,
        })

    return {"books": books}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
