#!/usr/bin/env python3
# /// script
# dependencies = ["genanki", "openai", "httpx", "python-dotenv"]
# ///

"""
Build an Anki deck from any of the four markdown tables.

Usage:
    uv run build_anki_deck.py --type vocabulary
    uv run build_anki_deck.py --type phrasal_verbs
    uv run build_anki_deck.py --type compound_nouns
    uv run build_anki_deck.py --type sentence_structures
    uv run build_anki_deck.py --type vocabulary --input tables/vocabulary.md --deck-name "My Vocab"

Audio (vocabulary / phrasal_verbs / compound_nouns only):
  1. Download US / UK audio from Free Dictionary API when available.
  2. Fall back to OpenAI TTS (two distinct random voices) for any accent missing.
  3. Sentence audio (first example) is always OpenAI TTS.
  Audio is cached in output_anki/audio/ — re-runs skip existing files.
"""

import argparse
import hashlib
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import genanki
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ROOT        = Path(__file__).parent
OUTPUT_DIR  = ROOT / "output_anki"
AUDIO_CACHE = OUTPUT_DIR / "audio"
TEMPLATES   = ROOT / "templates"

DICT_API   = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"
TTS_MODEL  = "tts-1"
TTS_VOICES = ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]


def _stable_id(seed: str) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)


@dataclass
class TableConfig:
    term_col: str
    anki_fields: list[str]
    table_cols: list[str]
    has_audio: bool
    pos_col: str | None
    model_name: str
    model_seed: str
    deck_seed: str
    default_input: str
    template_dir: str
    note_tags: list[str]


CONFIGS: dict[str, TableConfig] = {
    "vocabulary": TableConfig(
        term_col="word",
        anki_fields=[
            "Word", "Definition", "IPA", "PartOfSpeech", "Examples",
            "Quote", "Tags", "Synonyms", "Antonyms",
            "AudioAmerican", "AudioBritish", "SentenceAudio", "Image", "Sentence",
        ],
        table_cols=["word", "definition", "ipa", "partofspeech", "examples", "quotes", "tags", "synonyms", "antonyms"],
        has_audio=True,
        pos_col="partofspeech",
        model_name="Anki Skill — Vocabulary v1",
        model_seed="anki-skill-deck-vocabulary-model-v1",
        deck_seed="anki-skill-deck-vocabulary-deck-v1",
        default_input="tables/vocabulary.md",
        template_dir="vocabulary",
        note_tags=["vocabulary"],
    ),
    "phrasal_verbs": TableConfig(
        term_col="phrasal_verb",
        anki_fields=[
            "PhrasalVerb", "Definition", "IPA", "Examples",
            "Quote", "Tags", "Synonyms", "Antonyms",
            "AudioAmerican", "AudioBritish", "SentenceAudio", "Image", "Sentence",
        ],
        table_cols=["phrasal_verb", "definition", "ipa", "examples", "quotes", "tags", "synonyms", "antonyms"],
        has_audio=True,
        pos_col=None,
        model_name="Anki Skill — Phrasal Verbs v1",
        model_seed="anki-skill-deck-phrasal-verbs-model-v1",
        deck_seed="anki-skill-deck-phrasal-verbs-deck-v1",
        default_input="tables/phrasal_verbs.md",
        template_dir="phrasal_verbs",
        note_tags=["phrasal-verb"],
    ),
    "compound_nouns": TableConfig(
        term_col="compound_noun",
        anki_fields=[
            "CompoundNoun", "Definition", "IPA", "Examples",
            "Quote", "Tags", "Synonyms", "Antonyms",
            "AudioAmerican", "AudioBritish", "SentenceAudio", "Image", "Sentence",
        ],
        table_cols=["compound_noun", "definition", "ipa", "examples", "quotes", "tags", "synonyms", "antonyms"],
        has_audio=True,
        pos_col=None,
        model_name="Anki Skill — Compound Nouns v1",
        model_seed="anki-skill-deck-compound-nouns-model-v1",
        deck_seed="anki-skill-deck-compound-nouns-deck-v1",
        default_input="tables/compound_nouns.md",
        template_dir="compound_nouns",
        note_tags=["compound-noun"],
    ),
    "sentence_structures": TableConfig(
        term_col="structure",
        anki_fields=["Structure", "Meaning", "Examples", "Equivalent", "Tags"],
        table_cols=["structure", "meaning", "examples", "equivalent", "tags"],
        has_audio=False,
        pos_col=None,
        model_name="Anki Skill — Sentence Structures v1",
        model_seed="anki-skill-deck-sentence-structures-model-v1",
        deck_seed="anki-skill-deck-sentence-structures-deck-v1",
        default_input="tables/sentence_structures.md",
        template_dir="sentence_structures",
        note_tags=["sentence-structure"],
    ),
}


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_table(path: Path, config: TableConfig) -> list[dict]:
    expected = len(config.table_cols)
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[2:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in line.split("|")[1:-1]]
        if len(cells) < expected:
            continue
        rows.append(dict(zip(config.table_cols, cells[:expected])))
    return rows


# ── Field mapping ──────────────────────────────────────────────────────────────

def map_fields(row: dict, config: TableConfig,
               audio_us: str, audio_gb: str, audio_sent: str) -> list[str]:
    term     = row[config.term_col]
    sentence = row.get("examples", "").split(" · ")[0].strip()

    if config.term_col == "word":
        return [
            term, row["definition"], row["ipa"], row["partofspeech"],
            row["examples"], row["quotes"], row["tags"], row["synonyms"], row["antonyms"],
            audio_us, audio_gb, audio_sent, "", sentence,
        ]
    if config.term_col in ("phrasal_verb", "compound_noun"):
        return [
            term, row["definition"], row["ipa"],
            row["examples"], row["quotes"], row["tags"], row["synonyms"], row["antonyms"],
            audio_us, audio_gb, audio_sent, "", sentence,
        ]
    # sentence_structures
    return [row["structure"], row["meaning"], row["examples"], row["equivalent"], row["tags"]]


# ── Dictionary API ─────────────────────────────────────────────────────────────

def _accent(url: str) -> str | None:
    name = url.lower().split("/")[-1]
    if "-us." in name:
        return "us"
    if "-uk." in name or "-gb." in name:
        return "uk"
    return None


def fetch_dict_audio(word: str, pos: str | None) -> tuple[str | None, str | None]:
    try:
        resp = httpx.get(DICT_API.format(word), timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None, None

    entries = resp.json()
    if not isinstance(entries, list):
        return None, None

    def matches_pos(entry: dict) -> bool:
        if not pos:
            return True
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


def build_word_audio(client: OpenAI, term: str, pos: str | None) -> tuple[str, str]:
    slug    = _slug(term)
    us_path = AUDIO_CACHE / f"{slug}_us.mp3"
    uk_path = AUDIO_CACHE / f"{slug}_uk.mp3"

    us_url = uk_url = None
    if not us_path.exists() or not uk_path.exists():
        us_url, uk_url = fetch_dict_audio(term, pos)

    us_voice = None

    if not us_path.exists():
        if us_url:
            print("  US: dictionary")
            download_audio(us_url, us_path)
        else:
            us_voice = random.choice(TTS_VOICES)
            print(f"  US: TTS ({us_voice})")
            tts_generate(client, term, us_voice, us_path)

    if not uk_path.exists():
        if uk_url:
            print("  UK: dictionary")
            download_audio(uk_url, uk_path)
        else:
            voice = random.choice([v for v in TTS_VOICES if v != us_voice])
            print(f"  UK: TTS ({voice})")
            tts_generate(client, term, voice, uk_path)

    return _sound(us_path), _sound(uk_path)


def build_sentence_audio(client: OpenAI, term: str, examples: str) -> str:
    first = examples.split(" · ")[0].strip() if examples else ""
    if not first:
        return ""
    path = AUDIO_CACHE / f"{_slug(term)}_sent.mp3"
    if not path.exists():
        voice = random.choice(TTS_VOICES)
        print(f"  sentence: TTS ({voice})")
        tts_generate(client, first, voice, path)
    return _sound(path)


# ── Anki model ─────────────────────────────────────────────────────────────────

def build_model(config: TableConfig) -> genanki.Model:
    templates_dir = TEMPLATES / config.template_dir
    return genanki.Model(
        _stable_id(config.model_seed),
        config.model_name,
        fields=[{"name": f} for f in config.anki_fields],
        templates=[{
            "name": "Card 1",
            "qfmt": (templates_dir / "front.html").read_text(encoding="utf-8"),
            "afmt": (templates_dir / "back.html").read_text(encoding="utf-8"),
        }],
        css=(templates_dir / "style.css").read_text(encoding="utf-8"),
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build an Anki deck from a markdown table")
    parser.add_argument("--type", required=True, choices=list(CONFIGS.keys()),
                        help="Table type: vocabulary | phrasal_verbs | compound_nouns | sentence_structures")
    parser.add_argument("--input",     help="Markdown table path (default: tables/<type>.md)")
    parser.add_argument("--deck-name", help="Anki deck name (default: title-cased type)")
    parser.add_argument("--output",    help="Output .apkg path (default: output_anki/<type>.apkg)")
    args = parser.parse_args()

    config = CONFIGS[args.type]

    input_path  = Path(args.input) if args.input else ROOT / config.default_input
    deck_name   = args.deck_name or args.type.replace("_", " ").title()
    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"{args.type}.apkg"

    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_CACHE.mkdir(parents=True, exist_ok=True)

    rows = parse_table(input_path, config)
    print(f"Found {len(rows)} entries in {input_path}\n")

    client      = OpenAI() if config.has_audio else None
    model       = build_model(config)
    deck        = genanki.Deck(_stable_id(config.deck_seed), deck_name)
    media_files = []

    for i, row in enumerate(rows, 1):
        term = row[config.term_col]
        pos  = row.get(config.pos_col) if config.pos_col else None
        print(f"[{i}/{len(rows)}] {term}")

        if config.has_audio:
            audio_us, audio_gb = build_word_audio(client, term, pos)
            audio_sent         = build_sentence_audio(client, term, row.get("examples", ""))
            for field in (audio_us, audio_gb, audio_sent):
                if field:
                    media_files.append(str(AUDIO_CACHE / field[7:-1]))
        else:
            audio_us = audio_gb = audio_sent = ""

        deck.add_note(genanki.Note(
            model=model,
            fields=map_fields(row, config, audio_us, audio_gb, audio_sent),
            tags=config.note_tags,
        ))

    pkg = genanki.Package(deck)
    pkg.media_files = media_files
    pkg.write_to_file(str(output_path))

    print(f"\nDone — {len(rows)} notes → {output_path}")


if __name__ == "__main__":
    main()
