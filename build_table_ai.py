#!/usr/bin/env python3
# /// script
# dependencies = ["openai", "httpx", "python-dotenv", "pydantic"]
# ///

"""
Build vocabulary reference tables using OpenAI Responses API + Pydantic structured output.

Reads a word/phrase list, fetches Free Dictionary API data per term,
then sends batches of ≤5 terms to OpenAI and appends rows to the
markdown table immediately after each batch.

Usage:
    uv run build_table_ai.py --type vocabulary
    uv run build_table_ai.py --type phrasal_verbs
    uv run build_table_ai.py --type compound_nouns
    uv run build_table_ai.py --type sentence_structures
    uv run build_table_ai.py --type vocabulary --reading reading.md --batch-size 3 --model gpt-4.1
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

ROOT     = Path(__file__).parent
DICT_API = "https://freedictionaryapi.com/api/v1"
POS_MAP  = {"adj": "adjective", "n": "noun", "v": "verb", "adv": "adverb"}


# ── Pydantic output models ─────────────────────────────────────────────────────

class VocabRow(BaseModel):
    word:         str
    definition:   str
    ipa:          str
    partofspeech: str
    examples:     str = Field(description="Exactly 4 sentences joined by ' · '")
    quotes:       str
    tags:         str
    synonyms:     str
    antonyms:     str

class VocabResponse(BaseModel):
    rows: list[VocabRow]


class PhrasalVerbRow(BaseModel):
    phrasal_verb: str
    definition:   str
    ipa:          str
    examples:     str = Field(description="Exactly 4 sentences joined by ' · '")
    quotes:       str
    tags:         str
    synonyms:     str
    antonyms:     str

class PhrasalVerbResponse(BaseModel):
    rows: list[PhrasalVerbRow]


class CompoundNounRow(BaseModel):
    compound_noun: str
    definition:    str
    ipa:           str
    examples:      str = Field(description="Exactly 4 sentences joined by ' · '")
    quotes:        str
    tags:          str
    synonyms:      str
    antonyms:      str

class CompoundNounResponse(BaseModel):
    rows: list[CompoundNounRow]


class SentenceStructureRow(BaseModel):
    structure:  str
    meaning:    str
    examples:   str = Field(description="Exactly 4 sentences joined by ' · '")
    equivalent: str = Field(description="1–3 alternative structures joined by ', '; empty string if none")
    tags:       str

class SentenceStructureResponse(BaseModel):
    rows: list[SentenceStructureRow]


# ── Type config ────────────────────────────────────────────────────────────────

@dataclass
class TypeConfig:
    input_file:     str
    output_file:    str
    table_header:   str
    table_sep:      str
    fields:         list[str]        # column order — must match model field names
    response_model: type[BaseModel]  # Pydantic wrapper with rows: list[RowModel]
    system_prompt:  str
    has_dict_api:   bool = True
    api_pos_fixed:  str | None = None  # None = use POS from word list


# ── System prompts ─────────────────────────────────────────────────────────────

_VOCAB_SYSTEM = """\
You are a vocabulary table builder for an English language learning system.

You receive a batch of English words, each with:
- its part of speech
- raw data from the Free Dictionary API (may be null if not found)
- a reading text that provides topic context

For EACH word, produce one row by following these rules:

SENSE SELECTION
- Read all senses in entries[].senses[]
- Pick the ONE sense whose definition and examples best match the meaning used in the reading text
- Prefer everyday/general meanings over technical or specialized ones (avoid senses tagged with:
  mathematics, computing, medicine, botany, law, etc.)
- If multiple senses fit equally well, prefer the first one

FIELD RULES
- word: exactly as given in the input
- definition: the definition string of the chosen sense
- ipa: pronunciations[0].text from the entry; if empty, write the IPA transcription yourself
  (General American preferred)
- partofspeech: full word — noun / verb / adjective / adverb
- examples: ALWAYS exactly 4 sentences joined by " · "
    • take up to 2 from sense.examples[]
    • create custom sentences for the rest so the total is exactly 4
    • custom examples: same sense, relevant to the reading topic, natural and varied —
      do not copy the API examples
- quotes: sense.quotes[0].text (first quote only), or "" if none
- tags: sense.tags[] joined by ", ", or "" if none
- synonyms: up to 5 from sense.synonyms[]; if empty, fall back to entry.synonyms[]
- antonyms: up to 5 from sense.antonyms[]; if empty, fall back to entry.antonyms[]

FALLBACK (api_data is null or API returns an error)
- definition: write the dictionary definition of the word in English. Must be the word's own
  meaning (not a paraphrase of its use in the reading), but when the word has multiple meanings,
  pick the one that matches how it is used in the reading.
- ipa: write the IPA transcription yourself (General American preferred)
- partofspeech: use the type given in the input, mapped to full form
- examples: create 4 example sentences (same rules as above)
- tags: add relevant tags if applicable (e.g. countable, uncountable, formal, informal)
- quotes, synonyms, antonyms: leave empty

FORMATTING
- Escape any | character in field values as \\|
- Replace newlines with a single space — no multiline content in any field
- examples joined by " · "
"""

_PHRASAL_SYSTEM = """\
You are a vocabulary table builder for an English language learning system.

You receive a batch of English phrasal verbs, each with:
- raw data from the Free Dictionary API (may be null if the phrasal verb was not found)
- a reading text for topic context

For EACH phrasal verb, produce one row:

SENSE SELECTION (when api_data is not null)
- Read all senses in entries[].senses[]
- Pick the ONE sense whose definition best matches how the phrasal verb is used in the reading text
- Prefer everyday/general meanings over technical or specialized ones
- If multiple senses fit equally well, prefer the first one

FIELD RULES (when api_data is not null)
- phrasal_verb: exactly as given
- definition: the definition string of the chosen sense
- ipa: pronunciations[0].text from the entry; if empty, write the IPA transcription yourself
  (General American preferred)
- examples: ALWAYS exactly 4 sentences using the phrasal verb, joined by " · "
    • take up to 2 from sense.examples[]
    • create custom sentences for the rest so the total is exactly 4
    • custom examples: use the phrasal verb, same sense, relevant to reading topic,
      natural and varied — do not copy the API examples
- quotes: sense.quotes[0].text (first quote only), or "" if none
- tags: sense.tags[] joined by ", ", or "" if none
- ok from sense.synonyms[]; if empty, fall back to entry.synonyms[]
- antonyms: up to 5 from sense.antonyms[]; if empty, fall back to entry.antonyms[]

FALLBACK (api_data is null)
- definition: write the dictionary definition of the phrasal verb in English. Must be the
  phrasal verb's own meaning (not a paraphrase), but pick the meaning that matches the reading.
- ipa: write the IPA transcription yourself (General American preferred, for the base verb)
- examples: create 4 example sentences (same rules as above)
- tags: add relevant tags if applicable (e.g. informal, formal, transitive, intransitive,
  separable, inseparable)
- quotes, synonyms, antonyms: leave empty

FORMATTING
- Escape any | character in field values as \\|
- Replace newlines with a single space
- examples joined by " · "
"""

_COMPOUND_SYSTEM = """\
You are a vocabulary table builder for an English language learning system.

You receive a batch of English compound nouns, each with:
- raw data from the Free Dictionary API (often null — many compound nouns are not in the API)
- a reading text for topic context

For EACH compound noun, produce one row:

SENSE SELECTION (when api_data is not null)
- Read all senses in entries[].senses[]
- Pick the ONE sense whose definition best matches how the compound noun is used in the reading text
- Prefer everyday/general meanings over technical or specialized ones
- If multiple senses fit equally well, prefer the first one

FIELD RULES (when api_data is not null)
- compound_noun: exactly as given
- definition: the definition string of the chosen sense
- ipa: pronunciations[0].text from the entry; if empty, write the IPA transcription yourself
  (General American preferred)
- examples: ALWAYS exactly 4 sentences joined by " · "
    • take up to 2 from sense.examples[]
    • create custom sentences for the rest so the total is exactly 4
    • custom examples: same sense, relevant to reading topic, natural and varied —
      do not copy the API examples
- quotes: sense.quotes[0].text (first quote only), or "" if none
- tags: sense.tags[] joined by ", ", or "" if none
- synonyms: up to 5 from sense.synonyms[]; if empty, fall back to entry.synonyms[]
- antonyms: up to 5 from sense.antonyms[]; if empty, fall back to entry.antonyms[]

FALLBACK (api_data is null)
- definition: write the dictionary definition of the compound noun in English. Must be the
  compound noun's own meaning (not a paraphrase), but pick the meaning that matches the reading.
- ipa: write the IPA transcription yourself (General American preferred, transcribe both words)
- examples: create 4 example sentences (same rules as above)
- tags: add relevant tags if applicable (e.g. countable, uncountable, formal, informal)
- quotes, synonyms, antonyms: leave empty

FORMATTING
- Escape | as \\| in all field values
- Replace newlines with a single space
- examples joined by " · "
"""

_SENTENCE_SYSTEM = """\
You are a vocabulary table builder for an English language learning system.

You receive a batch of English sentence structures/patterns and a reading text for context.
There is no API data — generate all content yourself.

For EACH structure, produce one row:

FIELD RULES
- structure: exactly as given (e.g. "as ... as possible", "be required to + V")
- meaning: brief explanation of what this structure means and when/why to use it (1–2 sentences)
- examples: ALWAYS exactly 4 sentences joined by " · "
    • 2 examples relevant to the topic of the reading text
    • 2 examples on general everyday topics
    • all 4 must clearly demonstrate the structure in use — be natural and varied
- equivalent: 1–3 alternative structures or expressions that convey the same or very similar
  meaning, separated by ", "; leave empty if no clear equivalent exists
- tags: relevant usage tags joined by ", "
    • Formality: formal, informal, neutral
    • Mode: spoken, written, both
    • Exam relevance: IELTS writing, IELTS speaking, TOEIC, Cambridge
    • any other useful label

FORMATTING
- Escape | as \\| in all field values
- Replace newlines with a single space
- examples joined by " · "
- equivalent joined by ", "
- tags joined by ", "
"""


# ── Config registry ────────────────────────────────────────────────────────────

CONFIGS: dict[str, TypeConfig] = {
    "vocabulary": TypeConfig(
        input_file     = "output/vocabulary.md",
        output_file    = "tables/vocabulary.md",
        table_header   = "| word | definition | ipa | partofspeech | examples | quotes | tags | synonyms | antonyms |",
        table_sep      = "|------|------------|-----|--------------|----------|--------|------|----------|----------|",
        fields         = ["word", "definition", "ipa", "partofspeech", "examples", "quotes", "tags", "synonyms", "antonyms"],
        response_model = VocabResponse,
        system_prompt  = _VOCAB_SYSTEM,
        has_dict_api   = True,
        api_pos_fixed  = None,
    ),
    "phrasal_verbs": TypeConfig(
        input_file     = "output/phrasal_verbs.md",
        output_file    = "tables/phrasal_verbs.md",
        table_header   = "| phrasal_verb | definition | ipa | examples | quotes | tags | synonyms | antonyms |",
        table_sep      = "|--------------|------------|-----|----------|--------|------|----------|----------|",
        fields         = ["phrasal_verb", "definition", "ipa", "examples", "quotes", "tags", "synonyms", "antonyms"],
        response_model = PhrasalVerbResponse,
        system_prompt  = _PHRASAL_SYSTEM,
        has_dict_api   = True,
        api_pos_fixed  = "verb",
    ),
    "compound_nouns": TypeConfig(
        input_file     = "output/compound_nouns.md",
        output_file    = "tables/compound_nouns.md",
        table_header   = "| compound_noun | definition | ipa | examples | quotes | tags | synonyms | antonyms |",
        table_sep      = "|---------------|------------|-----|----------|--------|------|----------|----------|",
        fields         = ["compound_noun", "definition", "ipa", "examples", "quotes", "tags", "synonyms", "antonyms"],
        response_model = CompoundNounResponse,
        system_prompt  = _COMPOUND_SYSTEM,
        has_dict_api   = True,
        api_pos_fixed  = "noun",
    ),
    "sentence_structures": TypeConfig(
        input_file     = "output/sentence_structures.md",
        output_file    = "tables/sentence_structures.md",
        table_header   = "| structure | meaning | examples | equivalent | tags |",
        table_sep      = "|-----------|---------|----------|------------|------|",
        fields         = ["structure", "meaning", "examples", "equivalent", "tags"],
        response_model = SentenceStructureResponse,
        system_prompt  = _SENTENCE_SYSTEM,
        has_dict_api   = False,
    ),
}


# ── Dictionary API ─────────────────────────────────────────────────────────────

def _pick_pronunciation(prons: list[dict]) -> dict | None:
    for p in prons:
        if any("General American" in t for t in p.get("tags", [])):
            return p
    for p in prons:
        if any("Received Pronunciation" in t for t in p.get("tags", [])):
            return p
    return prons[0] if prons else None


def fetch_word(term: str, pos: str) -> dict | None:
    """Call Free Dictionary API filtered by POS. Returns dict or None on failure."""
    try:
        resp = httpx.get(f"{DICT_API}/entries/en/{term}", timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data    = resp.json()
    entries = data.get("entries", [])

    matched = [e for e in entries if e.get("partOfSpeech", "").lower() == pos.lower()]
    if not matched:
        matched = entries  # fallback: include all POS

    if not matched:
        return None

    for entry in matched:
        prons  = entry.get("pronunciations", [])
        picked = _pick_pronunciation(prons)
        entry["pronunciations"] = [picked] if picked else []

    return {"word": data.get("word"), "entries": matched}


def fetch_phrasal_verb(phrase: str) -> dict | None:
    """Try the full phrasal verb directly (with spaces). If not found, return None.
    Skill rule: do NOT fall back to the base verb — go straight to LLM fallback."""
    return fetch_word(phrase, "verb")


# ── Input parsing ──────────────────────────────────────────────────────────────

def parse_vocab_list(path: Path) -> list[dict[str, str]]:
    """'word (type)' lines → [{'term': str, 'pos': str}]."""
    items: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "(" in line and line.endswith(")"):
            term, _, rest = line.rpartition("(")
            abbr = rest.rstrip(")").strip()
            pos  = POS_MAP.get(abbr, abbr)
        else:
            term, pos = line, "noun"
        items.append({"term": term.strip(), "pos": pos})
    return items


def parse_simple_list(path: Path) -> list[dict[str, str]]:
    """One item per line → [{'term': str}]."""
    return [
        {"term": line.strip()}
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


# ── Prompt building ────────────────────────────────────────────────────────────

def build_user_message(
    batch:       list[dict[str, Any]],
    reading_text: str,
    type_name:   str,
) -> str:
    lines = ["## Reading Context", "", reading_text.strip(), "", "---", ""]

    n = len(batch)
    lines.append(f"## Terms to process ({n} item{'s' if n > 1 else ''})")
    lines.append("")

    for i, item in enumerate(batch, 1):
        term     = item["term"]
        pos      = item.get("pos", "")
        api_data = item.get("api_data")

        header = f"### {i}. {term} ({pos})" if pos else f"### {i}. {term}"
        lines.append(header)

        if type_name != "sentence_structures":
            lines.append("API data:")
            if api_data:
                lines.append("```json")
                lines.append(json.dumps(api_data, ensure_ascii=False, indent=2))
                lines.append("```")
            else:
                lines.append("null")

        lines.append("")

    return "\n".join(lines)


# ── Row formatting ─────────────────────────────────────────────────────────────

def _escape(val: str) -> str:
    return val.replace("|", "\\|").replace("\n", " ").strip()


def format_row(row: BaseModel, fields: list[str]) -> str:
    data  = row.model_dump()
    cells = " | ".join(_escape(data.get(f, "")) for f in fields)
    return f"| {cells} |"


# ── OpenAI call ────────────────────────────────────────────────────────────────

def call_openai(
    client:         OpenAI,
    model:          str,
    system_prompt:  str,
    user_message:   str,
    response_model: type[BaseModel],
) -> list[BaseModel]:
    """Call Responses API with Pydantic structured output. Returns list of row models."""
    response = client.responses.parse(
        model        = model,
        instructions = system_prompt,
        input        = [{"role": "user", "content": user_message}],
        text_format  = response_model,
    )
    return response.output_parsed.rows


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build vocabulary tables via OpenAI Responses API + Pydantic"
    )
    parser.add_argument("--type", required=True, choices=list(CONFIGS.keys()),
                        help="Table type to build")
    parser.add_argument("--reading",    default="reading.md",
                        help="Reading text file (default: reading.md)")
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Terms per OpenAI call, max 5 (default: 5)")
    parser.add_argument("--model",      default="gpt-4.1",
                        help="OpenAI model (default: gpt-4.1)")
    args = parser.parse_args()

    batch_size = min(args.batch_size, 5)
    config     = CONFIGS[args.type]

    # ── Validate inputs ────────────────────────────────────────────────────────
    reading_path = ROOT / args.reading
    input_path   = ROOT / config.input_file
    output_path  = ROOT / config.output_file

    if not reading_path.exists():
        sys.exit(f"Error: reading file not found: {reading_path}")
    if not input_path.exists():
        sys.exit(f"Error: input file not found: {input_path}")

    reading_text = reading_path.read_text(encoding="utf-8")

    # ── Parse word list ────────────────────────────────────────────────────────
    items = parse_vocab_list(input_path) if args.type == "vocabulary" \
            else parse_simple_list(input_path)
    print(f"Loaded {len(items)} items from {input_path}")

    # ── Init output file ───────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.exists():
        output_path.write_text(
            config.table_header + "\n" + config.table_sep + "\n",
            encoding="utf-8",
        )
        print(f"Created {output_path} with header")

    # ── Process in batches ─────────────────────────────────────────────────────
    client = OpenAI()
    total  = len(items)

    for batch_start in range(0, total, batch_size):
        batch_items = items[batch_start : batch_start + batch_size]
        batch_end   = batch_start + len(batch_items)
        print(f"\n[{batch_end}/{total}] Batch: {', '.join(it['term'] for it in batch_items)}")

        # Fetch Dict API data
        batch_with_data: list[dict[str, Any]] = []
        for item in batch_items:
            term = item["term"]

            if config.has_dict_api:
                if args.type == "phrasal_verbs":
                    api_data = fetch_phrasal_verb(term)
                elif args.type == "compound_nouns":
                    api_data = fetch_word(term, "noun") or \
                               fetch_word(term.replace(" ", "-"), "noun")
                else:
                    pos      = item.get("pos") or config.api_pos_fixed or "noun"
                    api_data = fetch_word(term, pos)

                print(f"  {term}: dict API → {'ok' if api_data else 'null (fallback)'}")
            else:
                api_data = None

            batch_with_data.append({**item, "api_data": api_data})

        # Build user message and call OpenAI
        user_msg = build_user_message(batch_with_data, reading_text, args.type)
        print(f"  → calling {args.model}...")

        try:
            rows = call_openai(
                client,
                model          = args.model,
                system_prompt  = config.system_prompt,
                user_message   = user_msg,
                response_model = config.response_model,
            )
        except Exception as e:
            print(f"  OpenAI error: {e}", file=sys.stderr)
            print(f"  Skipping batch {batch_start + 1}–{batch_end}", file=sys.stderr)
            continue

        if len(rows) != len(batch_items):
            print(f"  Warning: expected {len(batch_items)} rows, got {len(rows)}",
                  file=sys.stderr)

        # Append rows to output file
        with output_path.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(format_row(row, config.fields) + "\n")
                print(f"  ✓ {getattr(row, config.fields[0], '?')}")

    print(f"\nDone — {output_path}")


if __name__ == "__main__":
    main()
