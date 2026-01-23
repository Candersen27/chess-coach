"""
FastAPI backend for chess analysis using Stockfish.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any

from engine import ChessEngine


# Global engine instance
chess_engine = ChessEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifespan of the FastAPI application."""
    # Startup: Initialize the chess engine
    await chess_engine.start()
    print("Chess engine started successfully")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
