"""
Chess coaching module using Claude API.
"""

import os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

# Load .env from project root (two levels up from src/backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class ChessCoach:
    """AI chess coach powered by Claude."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def _get_system_prompt(self, board_context: dict = None) -> str:
        """Build the system prompt with optional board context."""
        base_prompt = """You are a friendly chess coach helping a student improve their game.

Your approach:
- Ask questions to understand what the student wants to work on
- Give concrete, actionable advice (not vague platitudes)
- Use the chessboard to illustrate points when helpful
- Be encouraging but honest about mistakes
- Reference established chess principles

You do NOT calculate tactics yourself — that's what the chess engine is for.
Your job is to explain concepts, guide learning, and help the student understand
WHY moves are good or bad.

Keep responses conversational and not too long. Ask follow-up questions to
understand what the student needs."""

        if board_context:
            base_prompt += f"\n\nCurrent board state:"
            base_prompt += f"\n- Position (FEN): {board_context.get('fen', 'starting position')}"
            if board_context.get('last_move'):
                base_prompt += f"\n- Last move: {board_context['last_move']}"
            if board_context.get('mode'):
                base_prompt += f"\n- Current mode: {board_context['mode']}"

        return base_prompt

    async def chat(self, message: str, conversation_history: list = None, board_context: dict = None) -> dict:
        """Send a message to the coach and get a response.

        Args:
            message: The user's message
            conversation_history: List of previous messages [{"role": ..., "content": ...}]
            board_context: Optional dict with fen, last_move, mode

        Returns:
            Dict with "message" (str) and "suggested_action" (None for now)
        """
        messages = []

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({
            "role": "user",
            "content": message
        })

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self._get_system_prompt(board_context),
            messages=messages
        )

        return {
            "message": response.content[0].text,
            "suggested_action": None
        }
