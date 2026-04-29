---
name: build-compound-nouns-table
description: Build a markdown compound nouns table from output/compound_nouns.md using the Free Dictionary API, one compound noun at a time
allowed-tools:
  - read
  - edit
  - exec
  - write
permissions:
  allow:
    - Write(tables/**)
    - Exec(uv run .devin/skills/build-compound-nouns-table/fetch_word.py *)
    - Exec(mkdir *)
triggers:
  - user
---

Build a compound nouns reference table at `tables/compound_nouns.md`.

Source files:
- `output/compound_nouns.md` — compound noun list (one per line, e.g. `credit check`)
- `reading.md` — the original reading text (used for context when choosing the right sense)

The fetch script is bundled inside this skill. Run it as:
```
uv run .devin/skills/build-compound-nouns-table/fetch_word.py "<compound noun>" noun
```

Note: the compound noun must be **quoted** because it contains a space.

Source code of the fetch script for reference:

@skills/build-compound-nouns-table/fetch_word.py

---

## Setup

1. Read `output/compound_nouns.md` to get the full list.
2. Read `reading.md` to understand the topic and context.
3. Run `mkdir -p tables` to ensure the output folder exists.
4. If `tables/compound_nouns.md` does not exist yet, create it and write this exact header as the first two lines:

```
| compound_noun | definition | ipa | examples | quotes | tags | synonyms | antonyms |
|---------------|------------|-----|----------|--------|------|----------|----------|
```

---

## Processing — do this for EVERY compound noun, one at a time

For each compound noun in the list, follow these steps **in order**, then **immediately append** the result row to `tables/compound_nouns.md` before moving to the next one.

### Step 1 — Fetch compound noun data

Try fetching the compound noun directly:
```
uv run .devin/skills/build-compound-nouns-table/fetch_word.py "<compound noun>" noun
```

Many compound nouns will NOT be found in the API. If the fetch fails (exit code 1), go straight to the **Fallback** section below.

### Step 2 — Choose the best sense

Read all senses in `senses[]`. Pick the **one sense** whose definition best matches how the compound noun is used in `reading.md`.

Criteria (in order of priority):
1. The definition matches the usage in the reading text
2. Prefer everyday/general meanings over technical or specialized ones
3. If multiple senses fit equally well, prefer the first one

### Step 3 — Collect fields from the chosen sense

From the chosen sense, collect:
- **definition** — the definition string
- **ipa** — `pronunciations[0].text` (from the entry); if empty, write the IPA transcription yourself (General American preferred)
- **api_examples** — up to 2 strings from `sense.examples[]`
- **quote** — `sense.quotes[0].text` (first quote only; leave empty if none)
- **tags** — `sense.tags[]` joined with `, ` (leave empty if none)
- **synonyms** — up to 5 from `sense.synonyms[]`; if empty, fall back to `entry.synonyms[]`
- **antonyms** — up to 5 from `sense.antonyms[]`; if empty, fall back to `entry.antonyms[]`

### Step 4 — Ensure exactly 4 examples

The `examples` cell must always contain exactly **4** example sentences that match the chosen sense.

- Take up to 2 examples from `sense.examples[]` (api_examples)
- Calculate how many custom examples are needed: `4 - len(api_examples)`
- Create that many custom example sentences so the total is exactly 4

Custom examples must:
- Use the compound noun with the same sense/meaning you selected in Step 2
- Be relevant to the topic of `reading.md` (e.g. renting an apartment, deposits, applications, maintenance)
- Be natural and varied — do not copy the API examples

### Step 5 — Build the row

Combine all **4 examples** into the `examples` cell, separated by ` · `

Escape any `|` characters in cell content with `\|`. Replace newlines in cell content with a space.

Write the row in this exact format:
```
| compound_noun | definition | ipa | examples | quote | tags | synonyms | antonyms |
```

### Step 6 — Append immediately

Append the completed row to `tables/compound_nouns.md` right away. Do not wait until all compound nouns are processed.

---

## Important rules

- Process compound nouns **in order** as they appear in `output/compound_nouns.md`
- Always **quote the compound noun** in the fetch command (it contains a space)
- Keep all cell content on a **single line** — no line breaks inside a cell
- Do not add extra blank lines between rows

## Fallback — when the API returns no data

Many compound nouns are not in the API. **Do NOT skip them.** Fill the row yourself:

- **definition** — write the dictionary definition of the compound noun in English. The definition must be the compound noun's **own meaning** (not a paraphrase of how it is used in the reading), but when the compound noun has multiple meanings, pick the one that matches how it is used in `reading.md`.
- **ipa** — write the IPA transcription yourself (General American preferred, transcribe both words)
- **examples** — create 4 example sentences (same rules as Step 4)
- **tags** — add relevant tags if applicable (e.g. countable, uncountable, formal, informal)
- **quotes, synonyms, antonyms** — leave empty

Then append the row as normal.
