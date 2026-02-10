"""
Chess coaching module using Claude API.
Integrates chess book knowledge and lesson plan generation.
"""

import os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from books import BookLibrary
from lesson import LessonManager, LessonPlan, extract_lesson_json

# Load .env from project root (two levels up from src/backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class ChessCoach:
    """AI chess coach powered by Claude with book knowledge."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

        # Load chess books
        self.library = BookLibrary()
        self.book_content = ""
        if self.library.get_book_titles():
            # Load the first available book for prompt inclusion
            title = self.library.get_book_titles()[0]
            self.book_content = self.library.format_for_prompt(title)
            print(f"Book content loaded: {len(self.book_content)} chars")

        # Lesson plan manager
        self.lesson_manager = LessonManager()

    def _get_system_prompt(self, board_context: dict = None, pattern_context: dict = None) -> list:
        """Build the system prompt with book content and board context.

        Returns a list of content blocks for prompt caching support.
        The book content block is marked as cacheable so subsequent
        calls reuse the cached prefix at reduced cost.
        """
        base_prompt = """You are a friendly, knowledgeable chess coach helping a student improve.

Your approach:
- Ask questions to understand what the student wants to work on
- Give concrete, actionable advice using specific positions
- Reference the chess literature when relevant — cite Capablanca's teachings naturally
- Be encouraging but honest about mistakes
- When the student is ready to practice, generate a structured lesson plan

You do NOT calculate tactics yourself — that's what the chess engine is for.
Your job is to explain concepts, guide learning, and help the student understand
WHY moves are good or bad.

Keep responses conversational and not too long. Ask follow-up questions to
understand what the student needs.

When the student agrees to practice something, generate a lesson plan in this JSON format.
Include the lesson plan JSON at the end of your message, after the marker [LESSON_PLAN].
Only generate a lesson plan when the student explicitly agrees to practice.

```json
{
  "topic": "...",
  "type": "endgame_practice|position_study|practice_game|tactics_drill|game_review",
  "source_reference": {"book": "...", "chapter": "...", "section": "..."},
  "goals": ["...", "..."],
  "activity": {
    "type": "...",
    "positions": [{"fen": "...", "instruction": "...", "goal": "..."}]
  },
  "teaching_notes": ["...", "..."],
  "success_criteria": "..."
}
```"""

        # Build system prompt as content blocks for caching
        system_blocks = []

        if self.book_content:
            # Book content block — marked for prompt caching
            system_blocks.append({
                "type": "text",
                "text": base_prompt + "\n\nYou have access to classic chess literature to ground your teaching:\n\n" + self.book_content,
                "cache_control": {"type": "ephemeral"}
            })
        else:
            system_blocks.append({
                "type": "text",
                "text": base_prompt,
            })

        # Board context block — changes each request, appended after cached content
        if board_context:
            context_text = "\n\nCurrent board state:"
            context_text += f"\n- Position (FEN): {board_context.get('fen', 'starting position')}"
            if board_context.get('last_move'):
                context_text += f"\n- Last move: {board_context['last_move']}"
            if board_context.get('mode'):
                context_text += f"\n- Current mode: {board_context['mode']}"
            system_blocks.append({
                "type": "text",
                "text": context_text,
            })

        # Pattern analysis context — appended when batch analysis data is available
        if pattern_context:
            recs = pattern_context.get("recommendations", [])
            patterns = pattern_context.get("tactical_patterns", {})
            phases = pattern_context.get("phase_stats", {})

            pattern_lines = [
                f"\n\n## Recent Game Analysis",
                f"You have analyzed {pattern_context.get('total_games', 0)} of the student's recent games.",
                f"Overall accuracy: {pattern_context.get('overall_accuracy', 0):.1f}%",
            ]

            if patterns:
                pattern_lines.append("\n### Tactical Weaknesses:")
                for ptype, instances in patterns.items():
                    readable = ptype.replace("_", " ")
                    game_count = len(set(i["game_index"] for i in instances))
                    pattern_lines.append(
                        f"- {readable.capitalize()}: {len(instances)} instances across {game_count} game(s)"
                    )

            if phases:
                pattern_lines.append("\n### Performance by Phase:")
                for phase_name, stats in phases.items():
                    pattern_lines.append(
                        f"- {phase_name.capitalize()}: {stats['avg_accuracy']:.1f}% accuracy, "
                        f"{stats['blunder_count']} blunders, {stats['mistake_count']} mistakes"
                    )

            if recs:
                pattern_lines.append("\n### Recommendations:")
                for rec in recs:
                    pattern_lines.append(f"- {rec}")

            pattern_lines.append(
                "\nUse this data to provide personalized coaching. "
                "Reference these specific patterns and recommend targeted practice."
            )

            system_blocks.append({
                "type": "text",
                "text": "\n".join(pattern_lines),
            })

        return system_blocks

    async def chat(self, message: str, conversation_history: list = None,
                   board_context: dict = None, pattern_context: dict = None) -> dict:
        """Send a message to the coach and get a response.

        Args:
            message: The user's message
            conversation_history: List of previous messages [{"role": ..., "content": ...}]
            board_context: Optional dict with fen, last_move, mode

        Returns:
            Dict with "message" (str) and "suggested_action" (dict or None)
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
            max_tokens=2048,
            system=self._get_system_prompt(board_context, pattern_context),
            messages=messages
        )

        raw_text = response.content[0].text

        # Check for lesson plan in response
        lesson_plan = None
        clean_message = raw_text

        plan_json = extract_lesson_json(raw_text)
        if plan_json:
            # Split message at the marker
            marker = "[LESSON_PLAN]"
            clean_message = raw_text.split(marker)[0].strip()
            lesson_plan = self.lesson_manager.create_lesson_from_response(plan_json)

        result = {
            "message": clean_message,
            "suggested_action": None
        }

        if lesson_plan:
            result["suggested_action"] = {
                "type": "start_lesson",
                "lesson_plan": lesson_plan.model_dump(mode="json")
            }

        return result
