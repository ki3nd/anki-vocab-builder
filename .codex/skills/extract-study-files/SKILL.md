---
name: extract-study-files
description: Extracts vocabulary, phrasal verbs, compound nouns, sentence structures, and grammar from a reading text into output/. Use when a new reading text is provided and study files need to be generated. Use when output/ is empty or missing and the user wants to start the learning workflow.
---

# Extract Study Files

## Overview

Read a reading text and extract 5 structured study files into `output/`. These files feed the downstream table-building skills. The quality of extraction here determines the quality of all subsequent study materials.

## When to Use

- A new reading text has been provided (e.g. `reading.md` updated)
- `output/` is empty, missing, or out of sync with the current reading text
- User asks to "start from the reading", "extract", or "generate study files"

**When NOT to use:** The output files already exist and the user only wants to build tables — go directly to the relevant build skill instead.

## Process

### Step 1 — Identify source file

Use the argument if provided, otherwise default to `reading.md`. Confirm the file exists before proceeding.

### Step 2 — Read for context

Read the full reading text to understand topic, register, and vocabulary level before extracting anything.

### Step 3 — Extract File 1: `output/vocabulary.md`

List vocabulary words at **B1 level and above**.

Rules:
- Skip basic words (articles, prepositions, auxiliary verbs: is, are, was, have, do, the, a, of, in, to, and, etc.)
- Include meaningful B1+ words — nouns, verbs, adjectives, adverbs — especially those common in everyday communication and English proficiency exams (IELTS, TOEIC, Cambridge)
- Write each word in **base/dictionary form** (`retain` not `retained`, `confirm` not `confirming`)
- Format per line: `word (type)` with type abbreviations `adj` `n` `v` `adv`, lowercase

Example:
```
smooth (adj)
retain (v)
income (n)
professionally (adv)
```

### Step 4 — Extract File 2: `output/phrasal_verbs.md`

List **phrasal verbs** worth learning — those common in everyday communication and likely in proficiency exams.

Rules:
- Phrasal verb = verb + particle acting as a unit with combined meaning
- Write in base form: `hold up`, `take place`, `check off`
- One per line, no definitions

### Step 5 — Extract File 3: `output/compound_nouns.md`

List **compound nouns** useful for English learners — those commonly used in everyday speaking and likely in proficiency exams.

Rules:
- Compound noun = two or more words functioning together as a single noun: `credit check`, `building owner`, `security deposit`
- Base form, lowercase, one per line, no definitions

### Step 6 — Extract File 4: `output/sentence_structures.md`

List **sentence structures and fixed expressions** useful for speaking or writing, and likely in proficiency exams.

Rules:
- Extract patterns as templates, not full sentences
- Use `...` for variable parts, `+` to indicate grammar following
- One per line

Example:
```
as ... as possible
be aware of ...
in order to + V
it is not unusual that + clause
```

### Step 7 — Extract File 5: `output/grammar.md`

List the **5–10 most important grammar structures** used in the text.

Rules:
- `#` heading per grammar name
- 2–4 example sentences taken **directly from the reading text** under each heading
- Focus on grammar common in general communication and proficiency exams

### Step 8 — Write all files

Create `output/` if it does not exist. Write all 5 files, overwriting any existing content.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll include basic words to be thorough" | Basic words waste table-building time and add noise — filter them out |
| "I'll write the word in its inflected form from the text" | Always use base/dictionary form so the fetch script finds it |
| "I'll add definitions to save time later" | Output files are lists only — definitions come from the API in the build step |
| "I'll combine all extractions in one pass" | Read the full text first for context, then extract each file separately |

## Red Flags

- Lines in vocabulary.md that include definitions or explanations
- Inflected forms (`retained`, `confirming`) instead of base forms
- Basic filler words appearing in the vocabulary list
- Fewer than 5 grammar structures extracted from a substantial text
- `output/` folder not created before writing

## Verification

- [ ] `output/vocabulary.md` exists with one `word (type)` per line, base forms only
- [ ] `output/phrasal_verbs.md` exists with one phrasal verb per line in base form
- [ ] `output/compound_nouns.md` exists with one compound noun per line
- [ ] `output/sentence_structures.md` exists with one template structure per line
- [ ] `output/grammar.md` exists with `#` headings and 2–4 direct quotes per grammar point
- [ ] No definitions or explanations appear in any list file (vocabulary, phrasal verbs, compound nouns, sentence structures)
