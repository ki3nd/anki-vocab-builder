# anki-skill

Language learning toolkit that extracts study materials from reading texts and builds vocabulary reference tables using the Free Dictionary API.

---

## Project Structure

```
anki-skill/
├── reading.md                   # Source reading text
├── fetch_word.py                # API fetch script (Free Dictionary API)
├── output/                      # Extracted study files
│   ├── vocabulary.md            # Word list: word (type) format
│   ├── phrasal_verbs.md         # Phrasal verbs
│   ├── sentence_structures.md  # Speaking/writing structures
│   └── grammar.md               # Grammar structures with examples
├── tables/                      # Generated reference tables
│   ├── vocabulary.md            # Full vocabulary table (markdown)
│   ├── phrasal_verbs.md         # Full phrasal verbs table (markdown)
│   ├── compound_nouns.md        # Full compound nouns table (markdown)
│   └── sentence_structures.md   # Full sentence structures table (markdown)
└── .devin/skills/
    ├── extract-study-files/     # Skill: extract 5 output files from reading text
    ├── build-vocab-table/       # Skill: build tables/vocabulary.md word by word
    ├── build-phrasal-verbs-table/ # Skill: build tables/phrasal_verbs.md
    ├── build-compound-nouns-table/ # Skill: build tables/compound_nouns.md
    └── build-sentence-structures-table/ # Skill: build tables/sentence_structures.md (no API)
```

---

## Scripts

### `fetch_word.py`

Fetches word data from the [Free Dictionary API](https://freedictionaryapi.com).

Copies exist:
- `fetch_word.py` — standalone script at project root (for manual use)
- `.devin/skills/build-vocab-table/fetch_word.py` — bundled copy (used by `/build-vocab-table`)
- `.devin/skills/build-phrasal-verbs-table/fetch_word.py` — bundled copy (used by `/build-phrasal-verbs-table`)
- `.devin/skills/build-compound-nouns-table/fetch_word.py` — bundled copy (used by `/build-compound-nouns-table`)

**Usage (standalone):**
```bash
uv run fetch_word.py <word> <partOfSpeech>
uv run fetch_word.py smooth adjective
uv run fetch_word.py income noun
uv run fetch_word.py retain verb
uv run fetch_word.py professionally adverb
```

**Usage (from skill):**
```bash
uv run .devin/skills/build-vocab-table/fetch_word.py <word> <partOfSpeech>
```

**partOfSpeech rules:** full word, lowercase, no abbreviations
- `noun` `verb` `adjective` `adverb`

**Pronunciation priority:** General American → Received Pronunciation → first available

**Output:** JSON with `word`, `source`, and `entries[]`. Each entry has `partOfSpeech`, `pronunciations` (filtered to 1), `senses`, `forms`, `synonyms`, `antonyms`.

If the partOfSpeech is not found, exits with code 1 and prints available parts of speech.

---

## Output Files

### `output/vocabulary.md`
One word per line: `word (type)` — base/dictionary form, abbreviated type (`adj`, `n`, `v`, `adv`).

### `output/phrasal_verbs.md`
One phrasal verb per line in base form (e.g. `take place`, `hold up`).

### `output/sentence_structures.md`
One structure/template per line (e.g. `as ... as possible`, `be required to + V`).

### `output/grammar.md`
`#` heading per grammar name, 2–4 example sentences from the reading text underneath.

---

## Tables

### `tables/vocabulary.md`

Markdown table with columns:

| Column | Source |
|--------|--------|
| `word` | from `output/vocabulary.md` |
| `definition` | best-matching sense from API |
| `ipa` | `pronunciations[0].text`; self-generated (General American) if empty |
| `partofspeech` | full word (noun, verb, adjective, adverb) |
| `examples` | always 4 examples (API + custom to fill), separated by ` · ` |
| `quotes` | first quote from the chosen sense |
| `tags` | sense tags (e.g. countable, uncountable, formal) |
| `synonyms` | up to 5 from sense or entry level |
| `antonyms` | up to 5 from sense or entry level |

### `tables/phrasal_verbs.md`

Markdown table with columns:

| Column | Source |
|--------|--------|
| `phrasal_verb` | from `output/phrasal_verbs.md` |
| `definition` | best-matching sense from API |
| `ipa` | `pronunciations[0].text`; self-generated (General American) if empty |
| `examples` | always 4 examples (API + custom to fill), separated by ` · ` |
| `quotes` | first quote from the chosen sense |
| `tags` | sense tags |
| `synonyms` | up to 5 from sense or entry level |
| `antonyms` | up to 5 from sense or entry level |

### `tables/compound_nouns.md`

Markdown table with columns:

| Column | Source |
|--------|--------|
| `compound_noun` | from `output/compound_nouns.md` |
| `definition` | best-matching sense from API, or self-generated (fallback is common) |
| `ipa` | `pronunciations[0].text`; self-generated (General American) if empty |
| `examples` | always 4 examples (API + custom to fill), separated by ` · ` |
| `quotes` | first quote from the chosen sense |
| `tags` | sense tags |
| `synonyms` | up to 5 from sense or entry level |
| `antonyms` | up to 5 from sense or entry level |

### `tables/sentence_structures.md`

Markdown table with columns (no API — all self-generated):

| Column | Description |
|--------|-------------|
| `structure` | the pattern template (e.g. `as ... as possible`) |
| `meaning` | brief explanation of when/why to use it |
| `examples` | always 4 examples (2 reading-topic + 2 general), separated by ` · ` |
| `equivalent` | 1–3 alternative structures with similar meaning |
| `tags` | formality, mode, exam relevance (IELTS, TOEIC, etc.) |

---

## Skills

### `/extract-study-files [reading_file]`

Reads a reading text (default: `reading.md`) and extracts all 5 study files into `output/`.

Invoke when: starting a new reading text and needing to generate study materials from scratch.

### `/build-vocab-table`

Reads `output/vocabulary.md` word by word, fetches each word from the API via `fetch_word.py`, selects the sense that best matches the context in `reading.md`, and appends each row to `tables/vocabulary.md` immediately.

Invoke when: `output/vocabulary.md` is ready and you want to build or extend the vocabulary table.

**Important:** This skill processes words one at a time and writes each row immediately — do not batch or defer writes.

### `/build-phrasal-verbs-table`

Reads `output/phrasal_verbs.md` one by one, fetches each phrasal verb from the API via `fetch_word.py` (with `verb` as partOfSpeech), selects the sense that best matches the context in `reading.md`, and appends each row to `tables/phrasal_verbs.md` immediately.

Invoke when: `output/phrasal_verbs.md` is ready and you want to build the phrasal verbs table.

**Fallback:** If fetching the full phrasal verb fails, tries the base verb (first word) and looks for a matching sense.

### `/build-compound-nouns-table`

Reads `output/compound_nouns.md` one by one, fetches each compound noun from the API via `fetch_word.py` (with `noun` as partOfSpeech), selects the sense that best matches the context in `reading.md`, and appends each row to `tables/compound_nouns.md` immediately.

Invoke when: `output/compound_nouns.md` is ready and you want to build the compound nouns table.

**Note:** Many compound nouns are not in the API. The fallback (self-generated definition, ipa, examples) will be used frequently for this skill.

### `/build-sentence-structures-table`

Reads `output/sentence_structures.md` one by one, and for each structure generates meaning, 4 examples, equivalent structures, and tags. Appends each row to `tables/sentence_structures.md` immediately.

Invoke when: `output/sentence_structures.md` is ready and you want to build the sentence structures table.

**No API needed.** All content is self-generated. Table columns: `structure`, `meaning`, `examples`, `equivalent`, `tags`.

---

## Conventions

- API calls use `uv run fetch_word.py` — `uv` handles dependency installation automatically
- The `tables/` directory is created if it does not exist
- Cells in markdown tables use ` · ` as an in-cell separator; `|` in content is escaped as `\|`
- Sense selection is done by reading comprehension against `reading.md` — prefer everyday meanings over technical/specialized ones
