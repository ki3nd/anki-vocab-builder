#!/usr/bin/env python3
# /// script
# dependencies = ["genanki", "openai", "httpx", "python-dotenv"]
# ///

"""
Build an Anki deck from a vocabulary markdown table.

Usage:
    uv run build_anki_vocab.py
    uv run build_anki_vocab.py --input tables/vocabulary.md --deck-name "My Vocab"

Audio strategy (per word):
  1. Download US / UK audio from the Free Dictionary API when available.
  2. Fall back to OpenAI TTS (two distinct random voices) for any accent missing.
  3. Sentence audio (first example) is always OpenAI TTS.

Audio is cached in output_anki/audio/ — re-runs skip existing files.
"""

import argparse
import hashlib
import random
import re
import sys
from pathlib import Path

import genanki
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
OUTPUT_DIR  = ROOT / "output_anki"
AUDIO_CACHE = OUTPUT_DIR / "audio"

# ── Anki model / deck IDs (stable across re-runs) ─────────────────────────────
def _stable_id(seed: str) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)

MODEL_ID = _stable_id("anki-skill-vocab-model-v1")
DECK_ID  = _stable_id("anki-skill-vocab-deck-v1")

# ── Constants ──────────────────────────────────────────────────────────────────
DICT_API   = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"
TTS_MODEL  = "tts-1"
TTS_VOICES = ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]

ANKI_FIELDS = [
    "Word", "Definition", "IPA", "PartOfSpeech", "Examples",
    "Quote", "Tags", "Synonyms", "Antonyms",
    "AudioAmerican", "AudioBritish", "SentenceAudio", "Image",
    "Sentence",
]


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_vocab_table(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[2:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in line.split("|")[1:-1]]
        if len(cells) < 9:
            continue
        rows.append({
            "word":         cells[0],
            "definition":   cells[1],
            "ipa":          cells[2],
            "partofspeech": cells[3],
            "examples":     cells[4],
            "quotes":       cells[5],
            "tags":         cells[6],
            "synonyms":     cells[7],
            "antonyms":     cells[8],
        })
    return rows


# ── Dictionary API ─────────────────────────────────────────────────────────────

def _accent(url: str) -> str | None:
    name = url.lower().split("/")[-1]
    if "-us." in name:
        return "us"
    if "-uk." in name or "-gb." in name:
        return "uk"
    return None


def fetch_dict_audio(word: str, pos: str) -> tuple[str | None, str | None]:
    """Return (us_url, uk_url) from the Free Dictionary API, or (None, None)."""
    try:
        resp = httpx.get(DICT_API.format(word), timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None, None

    entries = resp.json()
    if not isinstance(entries, list):
        return None, None

    def matches_pos(entry: dict) -> bool:
        return any(m.get("partOfSpeech", "").lower() == pos.lower()
                   for m in entry.get("meanings", []))

    preferred = [e for e in entries if matches_pos(e)] or entries

    us_url = uk_url = None
    for entry in preferred:
        for phonetic in entry.get("phonetics", []):
            url = phonetic.get("audio", "")
            if not url:
                continue
            accent = _accent(url)
            if accent == "us" and us_url is None:
                us_url = url
            elif accent == "uk" and uk_url is None:
                uk_url = url
        if us_url and uk_url:
            break

    return us_url, uk_url


def download_audio(url: str, dest: Path) -> bool:
    try:
        resp = httpx.get(url, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except httpx.HTTPError:
        return False


# ── TTS ────────────────────────────────────────────────────────────────────────

def tts_generate(client: OpenAI, text: str, voice: str, dest: Path) -> bool:
    try:
        with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL, voice=voice, input=text,
        ) as resp:
            resp.stream_to_file(str(dest))
        return True
    except Exception as e:
        print(f"  TTS error ({voice}): {e}", file=sys.stderr)
        return False


# ── Audio pipeline ─────────────────────────────────────────────────────────────

def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text).strip("_")[:60]


def _sound(path: Path) -> str:
    return f"[sound:{path.name}]" if path.exists() else ""


def build_word_audio(client: OpenAI, word: str, pos: str) -> tuple[str, str]:
    """Return (us_sound, uk_sound) Anki field values."""
    slug    = _slug(word)
    us_path = AUDIO_CACHE / f"{slug}_us.mp3"
    uk_path = AUDIO_CACHE / f"{slug}_uk.mp3"

    us_url = uk_url = None
    if not us_path.exists() or not uk_path.exists():
        us_url, uk_url = fetch_dict_audio(word, pos)

    us_voice = None

    if not us_path.exists():
        if us_url:
            print("  US: dictionary")
            download_audio(us_url, us_path)
        else:
            us_voice = random.choice(TTS_VOICES)
            print(f"  US: TTS ({us_voice})")
            tts_generate(client, word, us_voice, us_path)

    if not uk_path.exists():
        if uk_url:
            print("  UK: dictionary")
            download_audio(uk_url, uk_path)
        else:
            voice = random.choice([v for v in TTS_VOICES if v != us_voice])
            print(f"  UK: TTS ({voice})")
            tts_generate(client, word, voice, uk_path)

    return _sound(us_path), _sound(uk_path)


def build_sentence_audio(client: OpenAI, word: str, examples: str) -> str:
    """Return sentence_sound Anki field value for the first example."""
    first = examples.split(" · ")[0].strip() if examples else ""
    if not first:
        return ""

    path = AUDIO_CACHE / f"{_slug(word)}_sent.mp3"
    if not path.exists():
        voice = random.choice(TTS_VOICES)
        print(f"  sentence: TTS ({voice})")
        tts_generate(client, first, voice, path)

    return _sound(path)


# ── Anki model ─────────────────────────────────────────────────────────────────

def build_model(templates_dir: Path) -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Anki Skill — Vocab v1",
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
    parser = argparse.ArgumentParser(description="Build an Anki deck from a vocabulary markdown table")
    parser.add_argument("--input",     default=str(ROOT / "tables" / "vocabulary.md"),
                        help="Vocabulary markdown table path")
    parser.add_argument("--deck-name", help="Anki deck name (default: title-cased input stem)")
    parser.add_argument("--output",    help="Output .apkg path (default: output_anki/<stem>.apkg)")
    parser.add_argument("--templates", choices=["0", "1", "2", "3"], default="1",
                        help="Template set: 0 = legacy, 1 = vocab/phrasal/compound, 2 = sentence structures, 3 = sentence-first vocab")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    deck_name     = args.deck_name or input_path.stem.replace("_", " ").replace("-", " ").title()
    output_path   = Path(args.output) if args.output else OUTPUT_DIR / f"{input_path.stem}.apkg"
    templates_dir = ROOT / "templates" / f"template_{args.templates}"

    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_CACHE.mkdir(parents=True, exist_ok=True)

    rows = parse_vocab_table(input_path)
    print(f"Found {len(rows)} words in {input_path}\n")

    client      = OpenAI()
    model       = build_model(templates_dir)
    deck        = genanki.Deck(DECK_ID, deck_name)
    media_files = []

    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row['word']} ({row['partofspeech']})")

        audio_us, audio_gb = build_word_audio(client, row["word"], row["partofspeech"])
        audio_sent         = build_sentence_audio(client, row["word"], row["examples"])

        for field in (audio_us, audio_gb, audio_sent):
            if field:
                media_files.append(str(AUDIO_CACHE / field[7:-1]))

        sentence = row["examples"].split(" · ")[0].strip() if row["examples"] else ""

        deck.add_note(genanki.Note(
            model=model,
            fields=[
                row["word"], row["definition"], row["ipa"], row["partofspeech"],
                row["examples"], row["quotes"], row["tags"],
                row["synonyms"], row["antonyms"],
                audio_us, audio_gb, audio_sent,
                "",  # Image — fill manually in Anki
                sentence,
            ],
            tags=["vocab"],
        ))

    pkg = genanki.Package(deck)
    pkg.media_files = media_files
    pkg.write_to_file(str(output_path))

    print(f"\nDone — {len(rows)} notes → {output_path}")


if __name__ == "__main__":
    main()
