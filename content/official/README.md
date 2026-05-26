# Official Sets

Each `.lpset` file in this directory is automatically imported into the database
on every clean deploy (via `scripts/seed_official.py` in the CD pipeline).

## Format

A `.lpset` file is a ZIP archive containing:

```
my_set.lpset
├── manifest.json        ← required
├── audio/               ← optional
│   ├── word.mp3
│   └── word_ctx.mp3
└── images/              ← optional
    └── word.jpg
```

### manifest.json

```json
{
  "version": 1,
  "set": {
    "title": "My Set Title",
    "description": "Optional description",
    "source_lang": "en",
    "target_lang": "pl",
    "difficulty": 3
  },
  "items": [
    {
      "term": "serendipity",
      "context": "Finding something valuable by chance",
      "part_of_speech": "noun",
      "difficulty": 5,
      "lemma": "serendipity",
      "audio": "audio/serendipity.mp3",
      "context_audio": "audio/serendipity_ctx.mp3",
      "image": "images/serendipity.jpg",
      "translations": [
        {
          "lang": "pl",
          "term_trans": "zbiég szczęśliwych okoliczności",
          "context_trans": "Znalezienie czegoś cennego przez przypadek"
        }
      ]
    }
  ]
}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `version` | Yes | Must be `1` |
| `set.title` | Yes | Max 200 chars |
| `set.source_lang` | Yes | ISO 639-1 code (en, pl, de, ...) |
| `set.target_lang` | No | ISO 639-1 code; must differ from source_lang |
| `set.difficulty` | No | 1–7 |
| `item.term` | Yes | Max 500 chars |
| `item.context` | No | Example sentence, max 1000 chars |
| `item.audio` | No | Path inside ZIP |
| `item.context_audio` | No | Path inside ZIP |
| `item.image` | No | Path inside ZIP |
| `item.part_of_speech` | No | noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, article, other |
| `item.difficulty` | No | 1–7 |
| `item.lemma` | No | Base form |
| `translation.lang` | Yes | ISO 639-1 code |
| `translation.term_trans` | Yes | Max 500 chars |
| `translation.context_trans` | No | Max 1000 chars |

## Creating a .lpset file

```bash
# 1. Create directory structure
mkdir my_set
mkdir my_set/audio my_set/images

# 2. Write manifest.json (see format above)

# 3. Add media files

# 4. Package as ZIP with .lpset extension
cd my_set && zip -r ../my_set.lpset . && cd ..

# 5. Move to this directory
mv my_set.lpset content/official/
```

## Seeding

Re-run against any environment:

```bash
cd backend
uv run python scripts/seed_official.py
```

Sets already in the database (matched by title + source language) are skipped — safe to re-run.
