"""
FastAPI backend for chess analysis using Stockfish.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from engine import ChessEngine
from coach import ChessCoach


# Global instances
chess_engine = ChessEngine()
chess_coach = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifespan of the FastAPI application."""
    global chess_coach
    # Startup: Initialize the chess engine and coach
    await chess_engine.start()
    print("Chess engine started successfully")
    try:
        chess_coach = ChessCoach()
        print("Chess coach initialized successfully")
    except ValueError as e:
        print(f"Warning: Chess coach not available - {e}")
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


class BoardContext(BaseModel):
    """Board context for chat messages."""
    fen: Optional[str] = None
    last_move: Optional[str] = None
    mode: Optional[str] = None  # "analysis", "play", "idle"


class ChatMessage(BaseModel):
    """A single message in conversation history."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for chat with coach."""
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    board_context: Optional[BoardContext] = None


class ChatResponse(BaseModel):
    """Response model for chat with coach."""
    message: str
    suggested_action: Optional[dict] = None


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
        # Engine or other errors
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
        # Engine or other errors
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


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_coach(request: ChatRequest):
    """Chat with the chess coach.

    Args:
        request: Chat request with message, conversation history, and board context

    Returns:
        Coach's response message

    Raises:
        HTTPException: 503 if coach not initialized, 500 for API errors
    """
    if chess_coach is None:
        raise HTTPException(status_code=503, detail="Chess coach not available (check API key)")

    try:
        history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        board_ctx = request.board_context.model_dump() if request.board_context else None

        response = await chess_coach.chat(
            message=request.message,
            conversation_history=history,
            board_context=board_ctx
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
