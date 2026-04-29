#!/usr/bin/env python3
# /// script
# dependencies = ["httpx"]
# ///

"""
Fetch word information from Free Dictionary API.

Usage:
    uv run fetch_word.py <word> <partOfSpeech>

Examples:
    uv run fetch_word.py smooth adjective
    uv run fetch_word.py retain verb
    uv run fetch_word.py income noun
"""

import httpx
import json
import sys
import argparse

BASE_URL = "https://freedictionaryapi.com/api/v1"


def pick_pronunciation(pronunciations: list) -> dict | None:
    """
    Select a single pronunciation entry with the following priority:
    1. General American (first match)
    2. Received Pronunciation (first match)
    3. First entry available
    """
    if not pronunciations:
        return None

    for p in pronunciations:
        if any("General American" in tag for tag in p.get("tags", [])):
            return p

    for p in pronunciations:
        if any("Received Pronunciation" in tag for tag in p.get("tags", [])):
            return p

    return pronunciations[0]


def lookup(word: str, part_of_speech: str, language: str = "en") -> dict:
    url = f"{BASE_URL}/entries/{language}/{word}"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code} when looking up '{word}'", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: Could not reach the API — {e}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    entries = data.get("entries", [])

    # Filter entries by partOfSpeech (case-insensitive, full word match)
    matched = [
        e for e in entries
        if e.get("partOfSpeech", "").lower() == part_of_speech.lower()
    ]

    if not matched:
        available = sorted({e.get("partOfSpeech", "") for e in entries})
        print(
            f"No entries found for '{word}' with partOfSpeech='{part_of_speech}'.\n"
            f"Available parts of speech: {', '.join(available) or 'none'}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Process each matched entry: reduce pronunciations to 1
    for entry in matched:
        pronunciations = entry.get("pronunciations", [])
        selected = pick_pronunciation(pronunciations)
        entry["pronunciations"] = [selected] if selected else []

    return {
        "word": data.get("word"),
        "source": data.get("source"),
        "entries": matched,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Look up a word from the Free Dictionary API, filtered by part of speech."
    )
    parser.add_argument("word", help="The word to look up (e.g. smooth)")
    parser.add_argument(
        "part_of_speech",
        help="Part of speech in full lowercase (e.g. noun, verb, adjective, adverb)",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code (default: en)",
    )
    args = parser.parse_args()

    result = lookup(args.word, args.part_of_speech, args.language)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
