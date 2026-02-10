"""
Book library module for loading and querying structured chess books.
"""

import json
from pathlib import Path
from typing import List, Optional


class BookLibrary:
    """Manages chess books for inclusion in coaching prompts."""

    def __init__(self, books_dir: str = None):
        if books_dir is None:
            books_dir = str(Path(__file__).parent.parent.parent / "data" / "books")
        self.books_dir = Path(books_dir)
        self.books: dict = {}
        self._load_books()

    def _load_books(self):
        """Load all structured JSON books from the books directory."""
        for json_file in self.books_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                title = data["metadata"]["title"]
                self.books[title] = data
                print(f"Loaded book: {title} ({data['metadata']['total_sections']} sections, "
                      f"{data['metadata']['total_games']} games)")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load {json_file}: {e}")

    def get_book_titles(self) -> List[str]:
        """Return list of loaded book titles."""
        return list(self.books.keys())

    def get_section(self, book_title: str, section_number: int) -> Optional[dict]:
        """Get a specific section by number."""
        book = self.books.get(book_title)
        if not book:
            return None
        for part in book["parts"]:
            for chapter in part["chapters"]:
                for section in chapter["sections"]:
                    if section["section_number"] == section_number:
                        return section
        return None

    def search_topics(self, keywords: List[str]) -> List[dict]:
        """Find sections matching any of the given keywords."""
        results = []
        keywords_lower = [k.lower() for k in keywords]

        for title, book in self.books.items():
            for part in book["parts"]:
                for chapter in part["chapters"]:
                    for section in chapter["sections"]:
                        section_topics = [t.lower() for t in section.get("topics", [])]
                        section_title = section["title"].lower()

                        for kw in keywords_lower:
                            if (any(kw in t for t in section_topics)
                                    or kw in section_title):
                                results.append({
                                    "book": title,
                                    "chapter": chapter["title"],
                                    "section_number": section["section_number"],
                                    "section_title": section["title"],
                                    "topics": section["topics"],
                                })
                                break
        return results

    def format_for_prompt(self, book_title: str) -> str:
        """Format entire book content for inclusion in Claude's system prompt."""
        book = self.books.get(book_title)
        if not book:
            return ""

        meta = book["metadata"]
        lines = [
            f"=== {meta['title'].upper()} by {meta['author']} ({meta['year']}) ===",
            "",
        ]

        # Part I: Instructional content
        for part in book["parts"]:
            lines.append(f"PART {part['part_number']}")
            lines.append("")

            for chapter in part["chapters"]:
                lines.append(f"CHAPTER {chapter['chapter_number']}: {chapter['title']}")
                lines.append("")

                for section in chapter["sections"]:
                    lines.append(f"Section {section['section_number']}: {section['title']}")
                    lines.append("-" * (len(section['title']) + len(str(section['section_number'])) + 11))
                    lines.append(section["content"])
                    lines.append("")

        # Part II: Illustrative Games
        if book.get("illustrative_games"):
            lines.append("PART II: ILLUSTRATIVE GAMES")
            lines.append("")

            for game in book["illustrative_games"]:
                header = (f"Game {game['game_number']}: {game['white']} vs {game['black']} "
                          f"— {game['opening']} ({game['event']})")
                lines.append(header)
                lines.append("-" * len(header))
                lines.append(game["content"])
                lines.append("")

        return "\n".join(lines)

    def get_full_content(self, book_title: str) -> str:
        """Get entire book formatted for prompt inclusion (alias for format_for_prompt)."""
        return self.format_for_prompt(book_title)
