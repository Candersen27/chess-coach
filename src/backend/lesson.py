"""
Lesson plan generation and management module.
"""

import json
import re
from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class Position(BaseModel):
    fen: str
    instruction: str
    goal: Optional[str] = None
    hints: List[str] = []


class LessonActivity(BaseModel):
    type: Literal["practice_game", "position_study", "tactics_drill", "endgame_practice", "game_review"]
    positions: List[Position] = []
    coach_plays: Optional[Literal["white", "black"]] = None
    target_opening: Optional[str] = None
    pgn: Optional[str] = None


class SourceReference(BaseModel):
    book: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_hint: Optional[str] = None


class LessonPlan(BaseModel):
    id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    topic: str
    type: str
    source_reference: Optional[SourceReference] = None
    goals: List[str]
    activity: LessonActivity
    teaching_notes: List[str] = []
    success_criteria: Optional[str] = None


class LessonManager:
    """Manages lesson plan creation, tracking, and history."""

    def __init__(self):
        self.current_lesson: Optional[LessonPlan] = None
        self.lesson_history: List[LessonPlan] = []
        self._lesson_counter = 0

    def _generate_id(self) -> str:
        self._lesson_counter += 1
        date_str = datetime.now().strftime("%Y%m%d")
        return f"lesson_{date_str}_{self._lesson_counter:03d}"

    def create_lesson_from_response(self, plan_json: dict) -> Optional[LessonPlan]:
        """Create a LessonPlan from parsed JSON in Claude's response."""
        try:
            plan_json["id"] = self._generate_id()
            plan_json["created_at"] = datetime.now()
            lesson = LessonPlan(**plan_json)
            self.current_lesson = lesson
            return lesson
        except Exception as e:
            print(f"Failed to create lesson plan: {e}")
            return None

    def get_current_lesson(self) -> Optional[LessonPlan]:
        return self.current_lesson

    def complete_lesson(self, success: bool, notes: str = ""):
        """Mark current lesson complete and move to history."""
        if self.current_lesson:
            self.lesson_history.append(self.current_lesson)
            self.current_lesson = None


def extract_lesson_json(text: str) -> Optional[dict]:
    """Extract JSON lesson plan from text after [LESSON_PLAN] marker."""
    marker = "[LESSON_PLAN]"
    if marker not in text:
        return None

    json_text = text.split(marker, 1)[1].strip()

    # Try to find JSON object in the remaining text
    # Handle cases where JSON might be wrapped in markdown code blocks
    json_text = re.sub(r'^```json?\s*', '', json_text)
    json_text = re.sub(r'\s*```\s*$', '', json_text)

    # Find the JSON object boundaries
    brace_start = json_text.find('{')
    if brace_start == -1:
        return None

    depth = 0
    for i in range(brace_start, len(json_text)):
        if json_text[i] == '{':
            depth += 1
        elif json_text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(json_text[brace_start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None
