# anki-vocab-builder

Turn English reading texts into Anki flashcard decks, with definitions, IPA, examples, and audio.

## Workflow

```
reading.md → output/ (word lists) → tables/ (markdown) → output_anki/ (.apkg)
```

1. **Extract** — parse reading text into word lists (`/extract-study-files`)
2. **Build tables** — fetch definitions & IPA from [Free Dictionary API](https://freedictionaryapi.com) (`/build-vocab-table`, `/build-phrasal-verbs-table`, etc.)
3. **Build Anki** — generate `.apkg` decks with audio

```bash
uv run build_anki_deck.py --type vocabulary
uv run build_anki_deck.py --type phrasal_verbs
uv run build_anki_deck.py --type compound_nouns
uv run build_anki_deck.py --type sentence_structures    # no audio
```

## Requirements

- [uv](https://github.com/astral-sh/uv)
- [Devin CLI](https://cli.devin.ai/docs) or [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for extract & build tables
- `OPENAI_API_KEY` for TTS audio fallback

## License

MIT
