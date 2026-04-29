#!/usr/bin/env python3
# /// script
# dependencies = ["genanki", "python-dotenv"]
# ///

"""
Build an Anki deck from a sentence structures markdown table.

Usage:
    uv run build_anki_sentence_structures.py
    uv run build_anki_sentence_structures.py --input tables/sentence_structures.md

No audio, no API calls — all content comes from the table.
"""

import argparse
import hashlib
import sys
from pathlib import Path

import genanki
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent
DEFAULT_INPUT = ROOT / "tables" / "sentence_structures.md"
OUTPUT_DIR    = ROOT / "output_anki"

# ── Anki IDs ───────────────────────────────────────────────────────────────────
def _stable_id(seed: str) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)

MODEL_ID = _stable_id("anki-skill-sentence-model-v1")
DECK_ID  = _stable_id("anki-skill-sentence-deck-v1")

ANKI_FIELDS = ["Structure", "Meaning", "Examples", "Equivalent", "Tags"]


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_sentence_table(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[2:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        rows.append({
            "structure":  cells[0],
            "meaning":    cells[1],
            "examples":   cells[2],
            "equivalent": cells[3],
            "tags":       cells[4],
        })
    return rows


# ── Anki model ─────────────────────────────────────────────────────────────────

def build_model(templates_dir: Path) -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Anki Skill — Sentence Structures v1",
        fields=[{"name": f} for f in ANKI_FIELDS],
        templates=[{
            "name": "Card 1",
            "qfmt": (templates_dir / "front.html").read_text(encoding="utf-8"),
            "afmt": (templates_dir / "back.html").read_text(encoding="utf-8"),
        }],
        css=(templates_dir / "style.css").read_text(encoding="utf-8"),
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build an Anki deck from a sentence structures markdown table"
    )
    parser.add_argument("--input",     default=str(DEFAULT_INPUT),
                        help="Sentence structures markdown table path")
    parser.add_argument("--deck-name", help="Anki deck name (default: title-cased input stem)")
    parser.add_argument("--output",    help="Output .apkg path (default: output_anki/<stem>.apkg)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found. Run /build-sentence-structures-table first.", file=sys.stderr)
        sys.exit(1)

    deck_name     = args.deck_name or input_path.stem.replace("_", " ").replace("-", " ").title()
    output_path   = Path(args.output) if args.output else OUTPUT_DIR / f"{input_path.stem}.apkg"
    templates_dir = ROOT / "templates" / "templates_2"

    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = parse_sentence_table(input_path)
    print(f"Found {len(rows)} structures in {input_path}\n")

    model = build_model(templates_dir)
    deck  = genanki.Deck(DECK_ID, deck_name)

    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row['structure'][:60]}")
        deck.add_note(genanki.Note(
            model=model,
            fields=[
                row["structure"],
                row["meaning"],
                row["examples"],
                row["equivalent"],
                row["tags"],
            ],
            tags=["sentence-structure"],
        ))

    pkg = genanki.Package(deck)
    pkg.write_to_file(str(output_path))

    print(f"\nDone — {len(rows)} notes → {output_path}")


if __name__ == "__main__":
    main()
