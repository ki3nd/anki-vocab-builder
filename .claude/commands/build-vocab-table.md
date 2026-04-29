---
description: Build a markdown vocabulary table from output/vocabulary.md using the Free Dictionary API, one word at a time
---

Build a vocabulary reference table at `tables/vocabulary.md`.

Source files:
- `output/vocabulary.md` — word list (format: `word (type)`)
- `reading.md` — the original reading text (used for context when choosing the right sense)

The fetch script is bundled at `.claude/commands/fetch_word.py`. Run it as:
```
uv run .claude/commands/fetch_word.py <word> <partOfSpeech>
```

---

## Setup

1. Read `output/vocabulary.md` to get the full word list.
2. Read `reading.md` to understand the topic and context.
3. Run `mkdir -p tables` to ensure the output folder exists.
4. If `tables/vocabulary.md` does not exist yet, create it and write this exact header as the first two lines:

```
| word | definition | ipa | partofspeech | examples | quotes | tags | synonyms | antonyms |
|------|------------|-----|--------------|----------|--------|------|----------|----------|
```

---

## Word list format

Each line in `output/vocabulary.md` looks like: `word (type)`

Map the abbreviated type to full partOfSpeech for the fetch command:
- `adj` → `adjective`
- `n` → `noun`
- `v` → `verb`
- `adv` → `adverb`

---

## Processing — do this for EVERY word, one at a time

For each word in the list, follow these steps **in order**, then **immediately append** the result row to `tables/vocabulary.md` before moving to the next word.

### Step 1 — Fetch word data

Run:
```
uv run .claude/commands/fetch_word.py <word> <partOfSpeech>
```

The output is JSON with an `entries` array. Each entry has:
- `pronunciations` — already filtered to 1 item (General American preferred, then Received Pronunciation, then first available)
- `senses` — list of meaning objects, each with: `definition`, `examples`, `quotes`, `tags`, `synonyms`, `antonyms`

### Step 2 — Choose the best sense

Read all senses in `senses[]`. Pick the **one sense** whose definition and examples best match the meaning used in `reading.md`.

Criteria (in order of priority):
1. The definition matches the usage in the reading text
2. Prefer everyday/general meanings over technical or specialized ones (avoid senses tagged with: mathematics, computing, medicine, botany, law, etc.)
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
- Use the same sense/meaning you selected in Step 2
- Be relevant to the topic of `reading.md` (e.g. renting an apartment, deposits, applications, maintenance)
- Be natural and varied — do not copy the API examples

For example:
- API returns 2 examples → create 2 custom → total 4
- API returns 1 example → create 3 custom → total 4
- API returns 0 examples → create 4 custom → total 4

### Step 5 — Build the row

Combine all **4 examples** into the `examples` cell, separated by ` · `

Escape any `|` characters in cell content with `\|`. Replace newlines in cell content with a space.

Write the row in this exact format:
```
| word | definition | ipa | partofspeech | examples | quote | tags | synonyms | antonyms |
```

### Step 6 — Append immediately

Append the completed row to `tables/vocabulary.md` right away. Do not wait until all words are processed.

---

## Important rules

- Process words **in order** as they appear in `output/vocabulary.md`
- Keep all cell content on a **single line** — no line breaks inside a cell
- Do not add extra blank lines between rows

## Fallback — when the API returns no data

If the fetch script returns an error (e.g. wrong partOfSpeech, word not found, network error) and retrying with a related form also fails, **do NOT skip the word**. Instead, fill the row yourself:

- **definition** — write the dictionary definition of the word in English. The definition must be the word's **own meaning** (not a paraphrase of how it is used in the reading), but when the word has multiple meanings, pick the one that matches how it is used in `reading.md`.
- **ipa** — write the IPA transcription yourself (General American preferred)
- **partofspeech** — use the type from `output/vocabulary.md` mapped to full form
- **examples** — create 4 example sentences (same rules as Step 4)
- **tags** — add relevant tags if applicable (e.g. countable, uncountable, formal, informal)
- **quotes, synonyms, antonyms** — leave empty

Then append the row as normal.
