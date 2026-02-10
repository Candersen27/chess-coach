"""
Parse Chess Fundamentals by Capablanca into structured JSON.

Reads the raw Project Gutenberg text and extracts parts, chapters,
sections, and illustrative games into a structured format.
"""

import json
import re
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RAW_BOOK = PROJECT_ROOT / "data" / "books" / "chess_fundamentals_capablanca.txt"
OUTPUT_JSON = PROJECT_ROOT / "data" / "books" / "chess_fundamentals.json"

# Roman numeral conversion
ROMAN_MAP = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
             "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def roman_to_int(roman: str) -> int:
    return ROMAN_MAP.get(roman.strip(), 0)


def strip_gutenberg(text: str) -> str:
    """Remove Project Gutenberg header and footer."""
    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK CHESS FUNDAMENTALS ***"
    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK CHESS FUNDAMENTALS ***"

    start_idx = text.find(start_marker)
    if start_idx != -1:
        text = text[start_idx + len(start_marker):]

    end_idx = text.find(end_marker)
    if end_idx != -1:
        text = text[:end_idx]

    # Also strip the "End of Project Gutenberg's..." line
    end_line = "End of Project Gutenberg's Chess Fundamentals"
    end_idx = text.find(end_line)
    if end_idx != -1:
        text = text[:end_idx]

    return text.strip()


def strip_front_matter(text: str) -> str:
    """Remove everything before the actual content (title page, TOC, preface).

    The actual content starts at 'PART I' after the table of contents.
    We look for the PART I line that comes after the TOC section.
    """
    # Find "PART I" that appears as content start (after {3} page marker)
    # The TOC has "PART I" too, but the actual content one is preceded by a page number marker
    match = re.search(r'\{3\}\s*\n\s*\n\s*CHESS FUNDAMENTALS\s*\n\s*\n\s*PART I', text)
    if match:
        # Start from PART I
        part_start = text.find('PART I', match.start())
        return text[part_start:]

    # Fallback: find the second occurrence of "PART I" (first is TOC, second is content)
    first = text.find('PART I')
    if first != -1:
        second = text.find('PART I', first + 1)
        if second != -1:
            return text[second:]
    return text


def extract_topics(title: str, content: str) -> list:
    """Extract topic keywords from a section based on title and content."""
    topics = []
    title_lower = title.lower()

    # Topic mappings based on section titles
    topic_map = {
        "simple mates": ["checkmate", "rook endgame", "two bishops", "queen mate", "basic checkmate"],
        "pawn promotion": ["pawn endgame", "pawn promotion", "king and pawn"],
        "pawn endings": ["pawn endgame", "king and pawn", "pawn structure"],
        "winning positions": ["middle-game", "material advantage", "tactics"],
        "relative value": ["piece value", "material", "exchange"],
        "general strategy": ["opening", "opening strategy", "development"],
        "control of the centre": ["center control", "opening", "pawn center"],
        "traps": ["opening traps", "tactics", "blunders"],
        "cardinal principle": ["endgame principle", "king activity"],
        "classical ending": ["endgame", "classical technique", "rook endgame"],
        "passed pawn": ["passed pawn", "pawn endgame", "pawn promotion"],
        "first to queen": ["pawn race", "pawn promotion", "calculation"],
        "opposition": ["opposition", "king endgame", "pawn endgame"],
        "knight and bishop": ["minor pieces", "knight vs bishop", "piece value"],
        "mate with knight and bishop": ["checkmate", "knight and bishop mate", "basic endgame"],
        "queen against rook": ["queen vs rook", "endgame technique"],
        "attacking without": ["attack", "middle-game", "bishop attack"],
        "attacking with knights": ["knight attack", "middle-game", "tactics"],
        "indirect attack": ["indirect attack", "strategy", "middle-game"],
        "initiative": ["initiative", "tempo", "strategy"],
        "direct attacks": ["attack", "kingside attack", "tactics"],
        "threatened attack": ["positional play", "prophylaxis", "threat"],
        "relinquishing": ["initiative", "defense", "strategic retreat"],
        "cutting off": ["piece activity", "space", "restriction"],
        "motives criticised": ["game analysis", "decision making", "strategy"],
        "sudden attack": ["attack", "endgame", "tactical surprise"],
        "danger of a safe": ["defensive play", "overconfidence", "endgame"],
        "one rook and pawns": ["rook endgame", "rook and pawns"],
        "two rooks and pawns": ["rook endgame", "double rooks", "complex endgame"],
        "rook, bishop": ["rook endgame", "bishop vs knight", "complex endgame"],
        "salient points about pawns": ["pawn structure", "pawn play", "strategy"],
        "ruy lopez": ["ruy lopez", "opening", "pawn structure"],
        "influence of a hole": ["weak squares", "positional play", "pawn structure"],
    }

    for key, kw_topics in topic_map.items():
        if key in title_lower:
            topics = kw_topics
            break

    if not topics:
        # Fallback: extract from title words
        words = re.findall(r'[A-Za-z]+', title.lower())
        stop_words = {"the", "a", "an", "of", "in", "and", "or", "to", "with", "for", "from", "how", "some", "which"}
        topics = [w for w in words if w not in stop_words and len(w) > 2]

    return topics


def parse_book(text: str) -> dict:
    """Parse the book text into structured data."""
    lines = text.split('\n')
    total_lines = len(lines)

    parts = []
    illustrative_games = []

    current_part = None
    current_chapter = None
    current_section = None
    current_game = None

    in_part2 = False
    i = 0

    while i < total_lines:
        line = lines[i].rstrip()
        stripped = line.strip()

        # Skip page number markers like {3}, {4}, etc.
        if re.match(r'^\{?\d+\}?$', stripped):
            i += 1
            continue

        # Skip illustration markers
        if stripped.startswith('[Illustration'):
            i += 1
            continue

        # Detect PART markers
        part_match = re.match(r'^PART ([IVX]+)$', stripped)
        if part_match:
            part_num = roman_to_int(part_match.group(1))

            if part_num == 2:
                in_part2 = True
                # Save current section if any
                if current_section and current_chapter:
                    current_section["content"] = current_section["content"].strip()
                    current_chapter["sections"].append(current_section)
                    current_section = None
                if current_chapter and current_part:
                    current_part["chapters"].append(current_chapter)
                    current_chapter = None
                if current_part:
                    parts.append(current_part)
                    current_part = None
            else:
                current_part = {
                    "part_number": part_num,
                    "title": "",
                    "chapters": []
                }
            i += 1
            continue

        # Detect CHAPTER markers (only in Part I)
        chapter_match = re.match(r'^CHAPTER ([IVX]+)$', stripped)
        if chapter_match and not in_part2:
            # Save previous section/chapter
            if current_section and current_chapter:
                current_section["content"] = current_section["content"].strip()
                current_chapter["sections"].append(current_section)
                current_section = None
            if current_chapter and current_part:
                current_part["chapters"].append(current_chapter)

            chapter_num = roman_to_int(chapter_match.group(1))

            # Next non-empty line is the chapter title
            title = ""
            j = i + 1
            while j < total_lines:
                candidate = lines[j].strip()
                if candidate and not re.match(r'^\{?\d+\}?$', candidate):
                    title = candidate
                    break
                j += 1

            current_chapter = {
                "chapter_number": chapter_num,
                "title": title.title() if title else f"Chapter {chapter_num}",
                "sections": []
            }
            i = j + 1
            continue

        # Detect section markers (numbered sections like "1. SOME SIMPLE MATES")
        # Must have all-caps title with at least 2 words, exclude chess notation like "5. O - O"
        section_match = re.match(r'^(\d+)\.\s+([A-Z][A-Z\s\-_"\'v.,:;()\[\]]+)$', stripped)
        if section_match and not in_part2:
            candidate_title = section_match.group(2).strip()
            # Filter out chess notation like "O - O": must have at least 1 word of 4+ chars
            real_words = [w for w in re.findall(r'[A-Za-z]+', candidate_title) if len(w) >= 4]
            section_match = section_match if len(real_words) >= 1 else None
        if section_match and not in_part2:
            # Save previous section
            if current_section and current_chapter:
                current_section["content"] = current_section["content"].strip()
                current_chapter["sections"].append(current_section)

            sec_num = int(section_match.group(1))
            sec_title = section_match.group(2).strip()

            # Clean up title - remove trailing underscores from italic markers
            sec_title = re.sub(r'_+$', '', sec_title).strip()

            current_section = {
                "section_number": sec_num,
                "title": sec_title.title(),
                "topics": [],  # filled after content is collected
                "content": ""
            }
            i += 1
            continue

        # Detect game markers in Part II
        game_match = re.match(r'^GAME (\d+)\.\s+(.+)$', stripped)
        if game_match and in_part2:
            # Save previous game
            if current_game:
                current_game["content"] = current_game["content"].strip()
                illustrative_games.append(current_game)

            game_num = int(game_match.group(1))
            opening = game_match.group(2).strip()

            # Next line should be the event in parentheses
            event = ""
            j = i + 1
            while j < total_lines:
                candidate = lines[j].strip()
                if candidate:
                    event_match = re.match(r'^\((.+)\)$', candidate)
                    if event_match:
                        event = event_match.group(1)
                        j += 1
                    break
                j += 1

            # Next line should be "White: ... Black: ..."
            white = ""
            black = ""
            while j < total_lines:
                candidate = lines[j].strip()
                if candidate:
                    players_match = re.match(r'^White:\s*(.+?)\.\s*Black:\s*(.+?)\.?$', candidate)
                    if players_match:
                        white = players_match.group(1).strip()
                        black = players_match.group(2).strip()
                        j += 1
                    break
                j += 1

            current_game = {
                "game_number": game_num,
                "opening": opening.title(),
                "event": event,
                "white": white,
                "black": black,
                "content": ""
            }
            i = j
            continue

        # Accumulate content
        if in_part2 and current_game is not None:
            current_game["content"] += line + "\n"
        elif current_section is not None:
            current_section["content"] += line + "\n"

        i += 1

    # Finalize remaining structures
    if current_section and current_chapter:
        current_section["content"] = current_section["content"].strip()
        current_chapter["sections"].append(current_section)
    if current_chapter and current_part:
        current_part["chapters"].append(current_chapter)
    if current_part:
        parts.append(current_part)
    if current_game:
        current_game["content"] = current_game["content"].strip()
        illustrative_games.append(current_game)

    # Post-process: add topics and clean content
    for part in parts:
        for chapter in part["chapters"]:
            for section in chapter["sections"]:
                section["topics"] = extract_topics(section["title"], section["content"])
                # Clean up excessive blank lines
                section["content"] = re.sub(r'\n{3,}', '\n\n', section["content"])

    for game in illustrative_games:
        game["content"] = re.sub(r'\n{3,}', '\n\n', game["content"])

    # Count totals
    total_sections = sum(
        len(ch["sections"])
        for part in parts
        for ch in part["chapters"]
    )

    return {
        "metadata": {
            "title": "Chess Fundamentals",
            "author": "José Raúl Capablanca",
            "year": 1921,
            "source": "Project Gutenberg",
            "total_sections": total_sections,
            "total_games": len(illustrative_games)
        },
        "parts": parts,
        "illustrative_games": illustrative_games
    }


def main():
    print(f"Reading raw book from: {RAW_BOOK}")

    if not RAW_BOOK.exists():
        print(f"Error: Book file not found at {RAW_BOOK}")
        sys.exit(1)

    raw_text = RAW_BOOK.read_text(encoding="utf-8")
    print(f"Raw text: {len(raw_text)} characters, {len(raw_text.splitlines())} lines")

    # Strip Gutenberg header/footer
    text = strip_gutenberg(raw_text)
    print(f"After Gutenberg strip: {len(text)} characters")

    # Strip front matter (title page, TOC, preface)
    text = strip_front_matter(text)
    print(f"After front matter strip: {len(text)} characters")

    # Parse the book
    book = parse_book(text)

    # Print summary
    print(f"\n=== Parsing Results ===")
    print(f"Parts: {len(book['parts'])}")
    for part in book["parts"]:
        print(f"  Part {part['part_number']}: {len(part['chapters'])} chapters")
        for ch in part["chapters"]:
            print(f"    Chapter {ch['chapter_number']}: {ch['title']} ({len(ch['sections'])} sections)")
            for sec in ch["sections"]:
                print(f"      Section {sec['section_number']}: {sec['title']} [{', '.join(sec['topics'][:3])}]")

    print(f"\nIllustrative Games: {len(book['illustrative_games'])}")
    for game in book["illustrative_games"]:
        print(f"  Game {game['game_number']}: {game['white']} vs {game['black']} — {game['opening']} ({game['event']})")

    print(f"\nTotal sections: {book['metadata']['total_sections']}")
    print(f"Total games: {book['metadata']['total_games']}")

    # Write JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(book, f, indent=2, ensure_ascii=False)

    print(f"\nStructured JSON written to: {OUTPUT_JSON}")
    print(f"JSON file size: {OUTPUT_JSON.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
