# Vocabulary Card — Layout Reference

> Read this file alongside `DESIGN.md` to design a new template from scratch.
> `DESIGN.md` defines the visual language. This file defines the data model, card structure, and rendering rules.

---

## Anki Fields

These are the fields available in every vocabulary note. Templates are written in Anki's Mustache dialect.

| Field | Type | Content | Example |
|-------|------|---------|---------|
| `Word` | text | The vocabulary word | `volunteer` |
| `Definition` | text | Dictionary definition (plain text) | `One who offers themselves for service of their own free will` |
| `IPA` | text | IPA transcription, General American preferred | `/ˌvɑlənˈtɪɹ/` |
| `PartOfSpeech` | text | Full word: noun / verb / adjective / adverb | `noun` |
| `Examples` | HTML | 4 bulleted examples with inline audio tags, `<br>`-separated | `• Ex1 [sound:w_ex1.mp3]<br>• Ex2 [sound:w_ex2.mp3]<br>...` |
| `Quote` | text | A real-world usage quote from a corpus | `The largest age group for volunteers was 35–44.` |
| `Tags` | text | Comma-separated usage tags | `countable, formal` |
| `Synonyms` | text | Up to 5, comma-separated | `helper, contributor` |
| `Antonyms` | text | Up to 5, comma-separated | `opponent, critic` |
| `AudioAmerican` | sound | US pronunciation | `[sound:volunteer_us.mp3]` |
| `AudioBritish` | sound | UK pronunciation | `[sound:volunteer_uk.mp3]` |
| `SentenceAudio` | sound | TTS audio of the first example sentence | `[sound:volunteer_sent.mp3]` |
| `Image` | HTML | Optional image tag | `<img src="volunteer.jpg">` |
| `Sentence` | text | First example sentence (plain text, no audio tag) | `The volunteers meet every Sunday.` |
| `ExamplesAudio` | — | Reserved/empty — audio is embedded inline in `Examples` | `` |

### Notes on `Examples` field

- Separator in the source table (`tables/vocabulary.md`) is ` · `
- At build time (`build_anki_deck.py → _fmt_examples_with_audio`), each example is transformed to: `• {text} [sound:{slug}_ex{n}.mp3]`
- Each of the 4 examples has a distinct TTS voice (random, no repeat within one word)
- Anki renders `[sound:...]` tags as inline play buttons — no JavaScript needed

### Notes on `Sentence` field

- Always plain text — the first example without the bullet or the audio tag
- Used on the **front** card only
- `SentenceAudio` plays the same sentence

---

## Mustache Rules (Anki dialect)

- `{{Field}}` — render field as HTML (safe for `<br>`, `[sound:...]`, `<img>`)
- `{{text:Field}}` — render field as plain text (HTML-escaped)
- `{{#Field}} ... {{/Field}}` — show block only if field is non-empty
- `{{^Field}} ... {{/Field}}` — show block only if field is empty
- **No `{{! comment }}` support** — Anki does not support Mustache comments
- **No JavaScript** — templates must work without JS (AnkiDroid, AnkiMobile)

---

## Front Card

**Purpose:** Show the question — the learner sees the word and must recall its meaning.

```
┌─────────────────────────────────────────┐
│                                         │
│              volunteer                  │  ← Word (large, display font)
│           /ˌvɑlənˈtɪɹ/                 │  ← IPA (mono, muted)
│          🇺🇸 ▶   🇬🇧 ▶                  │  ← AudioAmerican + AudioBritish
│             [ noun ]                    │  ← PartOfSpeech (label)
│  ─────────────────────────────────────  │  ← divider
│                                         │
│  EXAMPLE  ▶                             │  ← "Example" label + SentenceAudio
│  The volunteers at the reserve meet     │  ← Sentence (italic, left-aligned)
│  up every Sunday to help its upkeep.   │
│                                         │
│  [image if present]                     │  ← Image (optional)
│                                         │
│  Laban · Cambridge · YouGlish · Images  │  ← search links (footer)
│                                         │
└─────────────────────────────────────────┘
```

### Front field visibility

| Field | Shown | Notes |
|-------|-------|-------|
| Word | ✅ | Always — this is the question |
| IPA | ✅ if non-empty | |
| AudioAmerican | ✅ if non-empty | Show both flags if both present; single flag if only one |
| AudioBritish | ✅ if non-empty | |
| PartOfSpeech | ✅ if non-empty | |
| Sentence | ✅ if non-empty | First example (plain text, italic) |
| SentenceAudio | ✅ if non-empty | Play button next to "Example" label |
| Image | ✅ if non-empty | |
| Definition | ❌ | Hidden — this is the answer |
| Examples | ❌ | Hidden — revealed on back |
| All meta | ❌ | Quote, Tags, Synonyms, Antonyms hidden |

---

## Back Card

**Purpose:** Reveal the full answer — definition, all examples with audio, meta.

```
┌─────────────────────────────────────────┐
│                                         │
│              volunteer                  │  ← Word (same as front)
│           /ˌvɑlənˈtɪɹ/                 │  ← IPA
│          🇺🇸 ▶   🇬🇧 ▶                  │  ← Audio
│             [ noun ]                    │  ← PartOfSpeech
│  ─────────────────────────────────────  │
│                                         │
│  One who enters into any service of     │  ← Definition
│  their own free will, esp. without pay. │
│                                         │
│  ─────────────────────────────────────  │
│                                         │
│  EXAMPLES                               │  ← section label (mono, uppercase)
│  • The volunteers at the reserve... ▶  │  ← example 1 + inline play button
│  • Sherri is looking for helpers... ▶  │  ← example 2 + inline play button
│  • Each volunteer spends an hour... ▶  │  ← example 3 + inline play button
│  • Being a volunteer helped her... ▶   │  ← example 4 + inline play button
│                                         │
│  "The largest age group for volunteers  │  ← Quote (italic, muted, optional)
│   was 35–44." — corpus                 │
│                                         │
│  TAGS                                   │  ← mono label (optional)
│  countable, formal                      │
│                                         │
│  SYNONYMS          ANTONYMS             │  ← 2-column grid (optional)
│  helper, giver     opponent             │
│                                         │
│  [image if present]                     │
│                                         │
│  Laban · Cambridge · YouGlish · Images  │
│                                         │
└─────────────────────────────────────────┘
```

### Back field visibility

| Field | Shown | Notes |
|-------|-------|-------|
| Word | ✅ | Repeated from front |
| IPA | ✅ if non-empty | |
| AudioAmerican / AudioBritish | ✅ if non-empty | Same as front |
| PartOfSpeech | ✅ if non-empty | |
| Definition | ✅ if non-empty | The main reveal |
| Examples | ✅ if non-empty | 4 bulleted lines with inline play buttons |
| Quote | ✅ if non-empty | Corpus quote, italicised, visually subtle |
| Tags | ✅ if non-empty | |
| Synonyms | ✅ if non-empty | 2-col grid with Antonyms if both present |
| Antonyms | ✅ if non-empty | Single block if no Synonyms |
| Image | ✅ if non-empty | |
| Sentence / SentenceAudio | ❌ | Already seen on front |

### Synonyms / Antonyms logic

Three cases must be handled explicitly (Anki Mustache has no `else`):

```
{{#Synonyms}}{{#Antonyms}}  → 2-column grid  {{/Antonyms}}{{/Synonyms}}
{{#Synonyms}}{{^Antonyms}}  → Synonyms only  {{/Antonyms}}{{/Synonyms}}
{{^Synonyms}}{{#Antonyms}}  → Antonyms only  {{/Antonyms}}{{/Synonyms}}
```

---

## Audio Rendering

Anki replaces `[sound:filename.mp3]` with a native play button. No HTML or JavaScript needed.

| Audio field | Where shown | Voice |
|-------------|------------|-------|
| `AudioAmerican` | Front + Back | Dictionary API (US) or TTS random voice |
| `AudioBritish` | Front + Back | Dictionary API (UK) or TTS random voice |
| `SentenceAudio` | Front only (next to Example label) | TTS random voice |
| Inline in `Examples` | Back only (end of each example line) | 4 distinct TTS voices |

---

## Template File Structure

Each template lives in `templates/{name}/` with three files:

```
templates/
└── {name}/
    ├── front.html   ← question side
    ├── back.html    ← answer side
    └── style.css    ← shared stylesheet (injected into both sides)
```

Register a new template by adding an entry to `CONFIGS` in `build_anki_deck.py`:

```python
"my_template": TableConfig(
    term_col="word",
    anki_fields=[
        "Word", "Definition", "IPA", "PartOfSpeech", "Examples",
        "Quote", "Tags", "Synonyms", "Antonyms",
        "AudioAmerican", "AudioBritish", "SentenceAudio", "Image", "Sentence",
        "ExamplesAudio",
    ],
    table_cols=["word", "definition", "ipa", "partofspeech", "examples", "quotes", "tags", "synonyms", "antonyms"],
    has_audio=True,
    pos_col="partofspeech",
    model_name="Anki Skill — My Template v1",
    model_seed="anki-skill-my-template-model-v1",   # unique string → stable ID
    deck_seed="anki-skill-my-template-deck-v1",     # unique string → stable ID
    default_input="tables/vocabulary.md",
    template_dir="my_template",
    note_tags=["vocabulary"],
),
```

Then build with:

```bash
uv run build_anki_deck.py --type my_template
```

---

## Design Constraints

- **No JavaScript** — all logic must be in Python (build time) or Mustache (render time)
- **No external fonts at runtime** — use system font stacks only (cards are viewed offline)
- **No box-shadows** — use background color contrast for depth
- **Night mode** — always include `.night_mode .card { ... }` overrides
- **Inline audio** — `[sound:...]` tags in `Examples` render as native Anki play buttons; do not try to style or reposition them with CSS



## Audio Replay Buttons
Design replay button
When audio or text to speech is included on your cards, Anki will show buttons you can click on to replay the audio.

If you prefer not to see the buttons, you can hide them in the preferences screen.

You can customize their appearance in your card styling, for example, to make them smaller and colored, you could use the following:


.replay-button svg {
  width: 20px;
  height: 20px;
}
.replay-button svg circle {
  fill: blue;
}
.replay-button svg path {
  stroke: white;
  fill: green;
}