---
name: build-sentence-structures-table
description: Builds a markdown sentence structures reference table from output/sentence_structures.md without any API calls — all content is self-generated. Use when output/sentence_structures.md is ready and tables/sentence_structures.md needs to be created or extended. Use when the user asks to "build the sentence structures table".
---

# Build Sentence Structures Table

## Overview

Process each structure in `output/sentence_structures.md` one at a time: write the meaning, generate exactly 4 examples (2 topic-relevant + 2 general), list equivalent structures, add tags, and append the row immediately. No API calls — all content is generated from your own knowledge.

## When to Use

- `output/sentence_structures.md` exists and is populated
- `tables/sentence_structures.md` is missing or incomplete
- User asks to build or continue the sentence structures table

**When NOT to use:** `output/sentence_structures.md` does not exist yet — run `extract-study-files` first.

## Process

### Setup

1. Read `output/sentence_structures.md` — get the full list
2. Read `reading.md` — understand topic and context for examples
3. Run `mkdir -p tables`
4. If `tables/sentence_structures.md` does not exist, create it with this exact header:

```
| structure | meaning | examples | equivalent | tags |
|-----------|---------|----------|------------|------|
```

### Per-structure loop — repeat for every entry

**Step 1 — Write the meaning**

Write a brief, clear explanation (1–2 sentences) of:
- What this structure means
- When and why to use it

Write in English.

**Step 2 — Create exactly 4 examples**

Write 4 example sentences:
- 2 relevant to the `reading.md` topic (e.g. renting an apartment, deposits, applications, maintenance)
- 2 on general everyday topics (to show the structure is versatile)
- All 4 must clearly demonstrate the structure in use
- Be natural and varied

**Step 3 — Write equivalent structures**

List 1–3 alternatives that convey the same or very similar meaning. Examples:
- `in order to + V` → `so as to + V`, `to + V (purpose)`
- `as ... as possible` → `as ... as one can`, `the most ... possible`
- `be required to + V` → `must + V`, `have to + V`, `be obliged to + V`

Leave empty if no clear equivalent exists.

**Step 4 — Add tags**

Tag with relevant usage context:
- Formality: `formal`, `informal`, `neutral`
- Mode: `spoken`, `written`, `both`
- Exam relevance: `IELTS writing`, `IELTS speaking`, `TOEIC`, `Cambridge`

**Step 5 — Build and append the row**

Join 4 examples with ` · `. Join equivalents with `, `. Join tags with `, `.
Escape `|` as `\|`. No line breaks in cells.

```
| structure | meaning | examples | equivalent | tags |
```

Append immediately. Do not wait for the full list.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write all rows then append at the end" | Append immediately after each structure — data loss risk otherwise |
| "I can't think of 2 general examples" | Every structure has general usage — consider greetings, work, travel, daily routines |
| "This structure has no equivalent" | Most structures have at least one alternative; only leave empty if truly none exist |
| "I'll write 3 examples from the reading topic" | The split must be exactly 2 topic-relevant + 2 general to show versatility |

## Red Flags

- Rows with fewer or more than 4 examples
- All 4 examples from the same topic (no general examples)
- Meanings that quote the reading text instead of explaining the structure
- Batch writes at the end instead of per-structure appends
- Line breaks inside table cells

## Verification

- [ ] `tables/sentence_structures.md` exists with header row
- [ ] Every structure from `output/sentence_structures.md` has a row
- [ ] Every row has exactly 4 examples separated by ` · `
- [ ] Examples split: 2 topic-relevant + 2 general
- [ ] All cell content is on a single line
- [ ] No API calls were made
