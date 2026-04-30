---
name: build-compound-nouns-table
description: Builds a markdown compound nouns reference table from output/compound_nouns.md using the Free Dictionary API, one compound noun at a time. Use when output/compound_nouns.md is ready and tables/compound_nouns.md needs to be created or extended. Use when the user asks to "build the compound nouns table". Fallback to self-generated content is common — most compound nouns are not in the API.
---

# Build Compound Nouns Table

## Overview

Process each compound noun in `output/compound_nouns.md` one at a time: fetch API data if available (most compound nouns will not be found), fall back to self-generated content when needed, and append the row immediately.

## When to Use

- `output/compound_nouns.md` exists and is populated
- `tables/compound_nouns.md` is missing or incomplete
- User asks to build or continue the compound nouns table

**When NOT to use:** `output/compound_nouns.md` does not exist yet — run `extract-study-files` first.

## Process

### Setup

1. Read `output/compound_nouns.md` — get the full list
2. Read `reading.md` — understand topic and context
3. Run `mkdir -p tables`
4. If `tables/compound_nouns.md` does not exist, create it with this exact header:

```
| compound_noun | definition | ipa | examples | quotes | tags | synonyms | antonyms |
|---------------|------------|-----|----------|--------|------|----------|----------|
```

### Per-compound-noun loop — repeat for every entry

**Step 1 — Fetch**

```bash
uv run .codex/skills/build-compound-nouns-table/fetch_word.py "<compound noun>" noun
```

Always quote the argument. If it fails (exit code 1), go directly to **Fallback** — do not try alternatives.

**Step 2 — Choose the best sense** *(API success only)*

Pick the one sense whose definition best matches how the compound noun is used in `reading.md`.

Priority:
1. Definition matches reading context
2. Everyday/general meaning over technical
3. If tied, prefer the first sense

**Step 3 — Collect fields** *(API success only)*

- `definition` — sense definition string
- `ipa` — `pronunciations[0].text`; if empty, generate IPA yourself (General American preferred, transcribe both words)
- `api_examples` — up to 2 from `sense.examples[]`
- `quote` — `sense.quotes[0].text` (empty if none)
- `tags` — `sense.tags[]` joined with `, ` (empty if none)
- `synonyms` — up to 5 from `sense.synonyms[]`, fallback to `entry.synonyms[]`
- `antonyms` — up to 5 from `sense.antonyms[]`, fallback to `entry.antonyms[]`

**Step 4 — Ensure exactly 4 examples**

- Take up to 2 from `api_examples`
- Create `4 - len(api_examples)` custom examples
- Custom examples must use the compound noun with the selected sense and be relevant to `reading.md`
- Do not copy API examples

**Step 5 — Build and append the row**

Join 4 examples with ` · `. Escape `|` as `\|`. No line breaks in cells.

```
| compound_noun | definition | ipa | examples | quote | tags | synonyms | antonyms |
```

Append immediately.

### Fallback — API returns no data (expected frequently)

Most compound nouns are not in the API. Do NOT skip them. Fill the row yourself:
- `definition` — the compound noun's own dictionary meaning in English; if multiple meanings, match `reading.md`
- `ipa` — write yourself (General American preferred; transcribe both words)
- `examples` — 4 custom sentences (same rules as Step 4)
- `tags` — e.g. countable, uncountable, formal, informal
- `quotes`, `synonyms`, `antonyms` — leave empty

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The API doesn't have it, I'll skip it" | Fallback is the norm for compound nouns — generate the row manually |
| "I'll only include compound nouns the API knows about" | Every entry in output/compound_nouns.md must appear in the table |
| "I'll write a paraphrase of how it's used in the reading" | Definition must be the compound noun's own meaning, not a reading summary |
| "I'll transcribe only the main word's IPA" | Transcribe both words in the compound noun |

## Red Flags

- Missing rows for compound nouns not found in the API
- IPA only for the first word, not both
- Definitions that are paraphrases of the reading instead of dictionary definitions
- Batch writes instead of immediate appends
- Fewer or more than 4 examples in any row

## Verification

- [ ] `tables/compound_nouns.md` exists with header row
- [ ] Every compound noun from `output/compound_nouns.md` has a row
- [ ] Every row has exactly 4 examples separated by ` · `
- [ ] No skipped entries (fallback used where API failed)
- [ ] All cell content is on a single line
