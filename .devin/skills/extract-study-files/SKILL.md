---
name: extract-study-files
description: Extract vocabulary, phrasal verbs, compound nouns, sentence structures, and grammar from a reading text into output/
argument-hint: "[reading_file]"
allowed-tools:
  - read
  - write
  - edit
permissions:
  allow:
    - Write(output/**)
triggers:
  - user
---

Read the reading file at `$1` (default: `reading.md` if no argument given).

Then extract and write **5 separate files** into the `output/` folder. Create the folder if it does not exist. Overwrite existing files.

---

## File 1 — `output/vocabulary.md`

List vocabulary words suitable for **B1 level and above**.

Rules:
- Skip very basic words (articles, prepositions, auxiliary verbs like: is, are, was, have, do, the, a, of, in, to, and, etc.)
- Include words that are meaningful to learn at B1+: nouns, verbs, adjectives, adverbs of substance — especially words commonly used in everyday communication and likely to appear in English proficiency exams (IELTS, TOEIC, Cambridge, etc.)
- Write each word in its **base/dictionary form** (e.g. `retain` not `retained`, `confirm` not `confirming`)
- One word per line in this exact format: `word (type)`
  - type abbreviations: `adj` `n` `v` `adv`
  - lowercase, no punctuation other than parentheses
- No definitions, no explanations — only the list

Example lines:
```
smooth (adj)
retain (v)
income (n)
professionally (adv)
```

---

## File 2 — `output/phrasal_verbs.md`

List **phrasal verbs** found in the reading text that are worth learning — especially those commonly used in everyday communication and likely to appear in English proficiency exams (IELTS, TOEIC, Cambridge, etc.).

Rules:
- Phrasal verb = verb + particle (preposition or adverb) acting as a unit with a combined meaning
- Write in base form (e.g. `hold up`, `take place`, `check off`)
- One phrasal verb per line
- No definitions, no explanations

---

## File 3 — `output/compound_nouns.md`

List **compound nouns** found in the reading text that are useful for English learners.

Rules:
- Compound noun = two or more words that function together as a single noun (e.g. `credit check`, `building owner`, `security deposit`)
- Focus on compound nouns that are **commonly used** in everyday speaking, communication, and likely to appear in English proficiency exams (IELTS, TOEIC, Cambridge, etc.)
- Write in base form, lowercase
- One compound noun per line
- No definitions, no explanations

Example lines:
```
credit check
building owner
security deposit
electric bill
interest rate
```

---

## File 4 — `output/sentence_structures.md`


List **sentence structures and fixed expressions** useful for speaking or writing in general communication, and likely to appear in English proficiency exams (IELTS, TOEIC, Cambridge, etc.).

Rules:
- Extract patterns, not full sentences — write as templates
- Use `...` for variable parts, `+` to indicate grammar following
- One structure per line

Example lines:
```
as ... as possible
be aware of ...
in order to + V
it is not unusual that + clause
be required to + V
```

---

## File 5 — `output/grammar.md`

List the **most important grammar structures** used in the text — focusing on grammar commonly used in general communication and likely to appear in English proficiency exams (IELTS, TOEIC, Cambridge, etc.).

Rules:
- Choose only key, useful grammar points (5–10 maximum) — do not list every grammar detail
- Use a `#` heading for each grammar name
- Under each heading, list 2–4 example sentences taken **directly from the reading text**
- Keep sentences as close to the original as possible

Example format:
```
# Passive Voice
The deposit must be returned within 3 weeks after you have vacated.
Your application will be professionally checked.

# Modal Verbs
You must expect to pay a deposit.
You should be prepared for the costs of application.
```
