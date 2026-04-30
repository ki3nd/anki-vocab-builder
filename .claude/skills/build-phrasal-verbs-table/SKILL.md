---
name: build-phrasal-verbs-table
description: Builds a markdown phrasal verbs reference table from output/phrasal_verbs.md using the Free Dictionary API, one phrasal verb at a time. Use when output/phrasal_verbs.md is ready and tables/phrasal_verbs.md needs to be created or extended. Use when the user asks to "build the phrasal verbs table".
---

# Build Phrasal Verbs Table

## Overview

Process each phrasal verb in `output/phrasal_verbs.md` one at a time: fetch API data for the full phrasal verb, choose the sense that best matches the reading context, generate exactly 4 examples, and append the row immediately. If the API returns no data, go directly to fallback — do not fetch the base verb.

## When to Use

- `output/phrasal_verbs.md` exists and is populated
- `tables/phrasal_verbs.md` is missing or incomplete
- User asks to build or continue the phrasal verbs table

**When NOT to use:** `output/phrasal_verbs.md` does not exist yet — run `extract-study-files` first.

## Process

### Setup

1. Read `output/phrasal_verbs.md` — get the full list
2. Read `reading.md` — understand topic and context
3. Run `mkdir -p tables`
4. If `tables/phrasal_verbs.md` does not exist, create it with this exact header:

```
| phrasal_verb | definition | ipa | examples | quotes | tags | synonyms | antonyms |
|--------------|------------|-----|----------|--------|------|----------|----------|
```

### Per-phrasal-verb loop — repeat for every entry

**Step 1 — Fetch**

Fetch the full phrasal verb:
```bash
uv run .claude/commands/fetch_word.py "<phrasal verb>" verb
```

Always quote the argument — it contains spaces.

If the fetch fails (exit code 1) or returns no data, skip to **Fallback** immediately. Do not fetch the base verb.

**Step 2 — Choose the best sense**

Pick the one sense whose definition best matches how the phrasal verb is used in `reading.md`.

Priority:
1. Definition matches reading context
2. Everyday/general meaning over technical
3. If tied, prefer the first sense

**Step 3 — Collect fields**

- `definition` — sense definition string
- `ipa` — `pronunciations[0].text`; if empty, generate IPA yourself (General American preferred)
- `api_examples` — up to 2 from `sense.examples[]`
- `quote` — `sense.quotes[0].text` (empty if none)
- `tags` — `sense.tags[]` joined with `, ` (empty if none)
- `synonyms` — up to 5 from `sense.synonyms[]`, fallback to `entry.synonyms[]`
- `antonyms` — up to 5 from `sense.antonyms[]`, fallback to `entry.antonyms[]`

**Step 4 — Ensure exactly 4 examples**

- Take up to 2 from `api_examples`
- Create `4 - len(api_examples)` custom examples
- Custom examples must use the phrasal verb (not just the base verb) with the selected sense
- Be relevant to the `reading.md` topic; do not copy API examples

**Step 5 — Build and append the row**

Join 4 examples with ` · `. Escape `|` as `\|`. No line breaks in cells.

```
| phrasal_verb | definition | ipa | examples | quote | tags | synonyms | antonyms |
```

Append immediately. Do not wait for the full list.

### Fallback — fetch fails or returns no data

Do NOT skip. Fill the row yourself:
- `definition` — the phrasal verb's own dictionary meaning in English; if multiple meanings, match `reading.md`
- `ipa` — write yourself (General American preferred, for the base verb)
- `examples` — 4 custom sentences using the full phrasal verb
- `tags` — e.g. informal, formal, transitive, intransitive, separable, inseparable
- `quotes`, `synonyms`, `antonyms` — leave empty

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The API doesn't have phrasal verbs, I'll skip them" | Go directly to fallback — generate the row manually |
| "I'll fetch the base verb since the full phrase isn't found" | Do not fetch the base verb — fallback immediately |
| "I'll write the example with just the base verb" | Custom examples must use the full phrasal verb form |
| "I'll process them all then write at the end" | Append immediately after each one — do not batch |

## Red Flags

- Rows skipped because the API had no result
- Examples that use only the base verb, not the phrasal verb
- Fewer or more than 4 examples in any row
- Phrasal verbs not quoted in the fetch command
- Batch writes instead of immediate appends

## Verification

- [ ] `tables/phrasal_verbs.md` exists with header row
- [ ] Every phrasal verb from `output/phrasal_verbs.md` has a row
- [ ] Every row has exactly 4 examples separated by ` · `
- [ ] No skipped entries (fallback used where API failed)
- [ ] All cell content is on a single line
