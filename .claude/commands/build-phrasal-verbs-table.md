---
description: Build a markdown phrasal verbs table from output/phrasal_verbs.md using the Free Dictionary API, one phrasal verb at a time
---

Build a phrasal verbs reference table at `tables/phrasal_verbs.md`.

Source files:
- `output/phrasal_verbs.md` — phrasal verb list (one per line, e.g. `hold up`)
- `reading.md` — the original reading text (used for context when choosing the right sense)

The fetch script is bundled at `.claude/commands/fetch_word.py`. Run it as:
```
uv run .claude/commands/fetch_word.py "<phrasal verb>" verb
```

Note: the phrasal verb must be **quoted** because it contains a space.

---

## Setup

1. Read `output/phrasal_verbs.md` to get the full list.
2. Read `reading.md` to understand the topic and context.
3. Run `mkdir -p tables` to ensure the output folder exists.
4. If `tables/phrasal_verbs.md` does not exist yet, create it and write this exact header as the first two lines:

```
| phrasal_verb | definition | ipa | examples | quotes | tags | synonyms | antonyms |
|--------------|------------|-----|----------|--------|------|----------|----------|
```

---

## Processing — do this for EVERY phrasal verb, one at a time

For each phrasal verb in the list, follow these steps **in order**, then **immediately append** the result row to `tables/phrasal_verbs.md` before moving to the next one.

### Step 1 — Fetch phrasal verb data

First, try fetching the phrasal verb directly:
```
uv run .claude/commands/fetch_word.py "<phrasal verb>" verb
```

If that fails (exit code 1), fall back to fetching the **base verb** (first word of the phrasal verb) and look for a sense whose definition or examples mention the full phrasal usage:
```
uv run .claude/commands/fetch_word.py "<base verb>" verb
```

### Step 2 — Choose the best sense

Read all senses in `senses[]`. Pick the **one sense** whose definition best matches how the phrasal verb is used in `reading.md`.

Criteria (in order of priority):
1. The definition matches the usage in the reading text
2. Prefer everyday/general meanings over technical or specialized ones
3. If multiple senses fit equally well, prefer the first one

### Step 3 — Collect fields from the chosen sense

From the chosen sense, collect:
- **definition** — the definition string
- **ipa** — `pronunciations[0].text`; if `pronunciations` is empty, generate IPA yourself (General American preferred)
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
- Use the phrasal verb with the same sense/meaning you selected in Step 2
- Be relevant to the topic of `reading.md` (e.g. renting an apartment, deposits, applications, maintenance)
- Be natural and varied — do not copy the API examples

### Step 5 — Build the row

Combine all **4 examples** into the `examples` cell, separated by ` · `

Escape any `|` characters in cell content with `\|`. Replace newlines in cell content with a space.

Write the row in this exact format:
```
| phrasal_verb | definition | ipa | examples | quote | tags | synonyms | antonyms |
```

### Step 6 — Append immediately

Append the completed row to `tables/phrasal_verbs.md` right away. Do not wait until all phrasal verbs are processed.

---

## Important rules

- Process phrasal verbs **in order** as they appear in `output/phrasal_verbs.md`
- Always **quote the phrasal verb** in the fetch command (it contains a space)
- Keep all cell content on a **single line** — no line breaks inside a cell
- Do not add extra blank lines between rows

## Fallback — when the API returns no data

If both the direct fetch and the base-verb fallback fail, **do NOT skip the phrasal verb**. Instead, fill the row yourself:

- **definition** — write the dictionary definition of the phrasal verb in English. The definition must be the phrasal verb's **own meaning** (not a paraphrase of how it is used in the reading), but when the phrasal verb has multiple meanings, pick the one that matches how it is used in `reading.md`.
- **ipa** — write the IPA transcription yourself (General American preferred, for the base verb)
- **examples** — create 4 example sentences (same rules as Step 4)
- **tags** — add relevant tags if applicable (e.g. informal, formal, transitive, intransitive, separable, inseparable)
- **quotes, synonyms, antonyms** — leave empty

Then append the row as normal.
