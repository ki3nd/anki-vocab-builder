---
name: build-vocab-table
description: Builds a markdown vocabulary reference table from output/vocabulary.md using the Free Dictionary API, one word at a time. Use when output/vocabulary.md is ready and tables/vocabulary.md needs to be created or extended. Use when the user asks to "build the vocab table" or "process the word list".
---

# Build Vocab Table

## Overview

Process each word in `output/vocabulary.md` one at a time: fetch API data, choose the sense that best matches the reading context, generate exactly 4 examples, and append the row immediately. Never batch or defer writes.

## When to Use

- `output/vocabulary.md` exists and is populated
- `tables/vocabulary.md` is missing or incomplete
- User asks to build, extend, or continue the vocabulary table

**When NOT to use:** `output/vocabulary.md` does not exist yet — run `extract-study-files` first.

## Process

### Setup

1. Read `output/vocabulary.md` — get the full word list
2. Read `reading.md` — understand topic and context for sense selection
3. Run `mkdir -p tables`
4. If `tables/vocabulary.md` does not exist, create it with this exact header:

```
| word | definition | ipa | partofspeech | examples | quotes | tags | synonyms | antonyms |
|------|------------|-----|--------------|----------|--------|------|----------|----------|
```

### Per-word loop — repeat for every word

**Step 1 — Map type to partOfSpeech**

Each line is `word (type)`. Map abbreviation to full form:
- `adj` → `adjective` | `n` → `noun` | `v` → `verb` | `adv` → `adverb`

**Step 2 — Fetch**

```bash
uv run .claude/commands/fetch_word.py <word> <partOfSpeech>
```

Output is JSON with `entries[]`. Each entry has `pronunciations` (pre-filtered to 1) and `senses[]`.

**Step 3 — Choose the best sense**

Pick the one sense whose definition best matches the word's usage in `reading.md`.

Priority:
1. Definition matches reading context
2. Everyday/general meaning over technical (avoid: mathematics, computing, medicine, botany, law)
3. If tied, prefer the first sense

**Step 4 — Collect fields**

- `definition` — sense definition string
- `ipa` — `pronunciations[0].text`
- `api_examples` — up to 2 from `sense.examples[]`
- `quote` — `sense.quotes[0].text` (empty if none)
- `tags` — `sense.tags[]` joined with `, ` (empty if none)
- `synonyms` — up to 5 from `sense.synonyms[]`, fallback to `entry.synonyms[]`
- `antonyms` — up to 5 from `sense.antonyms[]`, fallback to `entry.antonyms[]`

**Step 5 — Ensure exactly 4 examples**

- Take up to 2 from `api_examples`
- Create `4 - len(api_examples)` custom examples
- Custom examples must use the selected sense and be relevant to the `reading.md` topic
- Do not copy API examples

**Step 6 — Build and append the row**

Join 4 examples with ` · `. Escape `|` as `\|`. No line breaks in cells.

```
| word | definition | ipa | partofspeech | examples | quote | tags | synonyms | antonyms |
```

Append immediately. Do not wait for the full list.

### Fallback — API returns no data

Do NOT skip the word. Fill the row yourself:
- `definition` — write the word's own dictionary meaning in English; if multiple meanings, match `reading.md`
- `ipa` — write yourself (General American preferred)
- `partofspeech` — from the type mapping
- `examples` — 4 custom sentences (same rules as Step 5)
- `tags` — relevant tags (countable, uncountable, formal, informal)
- `quotes`, `synonyms`, `antonyms` — leave empty

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll batch all words and write at the end" | One crash or timeout loses all work — append immediately after each word |
| "I'll skip this word, the API returned nothing" | Fallback exists for this — generate the row manually |
| "I'll use the most common definition" | Choose the sense that matches `reading.md` context, not the most popular one |
| "I'll include more than 2 API examples" | Cap at 2 from API, fill the rest as custom — always exactly 4 total |

## Red Flags

- Rows with fewer or more than 4 examples
- Words skipped because the API failed
- Definitions that don't match the reading context
- Multiple rows written at once instead of one-at-a-time
- Line breaks inside a table cell

## Verification

- [ ] `tables/vocabulary.md` exists with header row
- [ ] Every word from `output/vocabulary.md` has a row
- [ ] Every row has exactly 4 examples separated by ` · `
- [ ] No skipped words (fallback used where API failed)
- [ ] All cell content is on a single line
