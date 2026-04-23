# Note Type: Japanese_Mined_Vocab

## Overview

This Note Type is designed for sentence-mining Japanese vocabulary. Each Note captures a word discovered in context, along with the sentence it was mined from, enabling two complementary Card Types: reading comprehension and active recall (production).

---

## Target Deck

`Japanese::Vocabulary`

---

## ID Strategy

**User-defined unique identifier in the first field (`VocabID`) using a namespaced index.**

- Each CSV entry file must be prefixed with a 3-digit index (e.g., `001_SourceTitle.csv`).
- Each Note must have a stable ID following the format `{FileIndex}_{Sequence}` (e.g., `001_0001`, `001_0152`).
- When importing via CSV with "Update existing notes where first field matches", Anki will match on `VocabID` to update existing Notes rather than creating duplicates.
- Never leave `VocabID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name            | Purpose                                                                                     |
|---|-----------------------|---------------------------------------------------------------------------------------------|
| 1 | `VocabID`             | Unique stable identifier for idempotent CSV imports (e.g., `001_0152`).                     |
| 2 | `TargetWord`          | Dictionary form of the vocabulary word (e.g., `始まる`).                                   |
| 3 | `Reading`             | Kana reading or furigana (e.g., `はじまる`).                                                |
| 4 | `Meaning`             | Definition in the learner's native language (e.g., `to begin; to start`).                  |
| 5 | `Sentence`            | The mined Japanese sentence. The conjugated target word must be wrapped in `<b>` tags (e.g., `もう一時間めが<b>始まっています</b>。`). |
| 6 | `SentenceTranslation` | Full translation of the mined sentence into the learner's native language.                  |
| 7 | `Notes`               | Grammar nuances, kanji breakdowns, transitive/intransitive pairs, usage notes, etc.        |
| 8 | `Audio`               | Native pronunciation audio file reference (e.g., `[sound:jp_0152.mp3]`). Optional.        |

---

## Card Types

1. **Comprehension** — Read the sentence in context; recognize and understand the bolded target word.
2. **Production** — Given the sentence with the target word blanked out and a native-language hint, recall the correct Japanese word.

---

## Data Entry Rules

- The conjugated form of the target word in `Sentence` must always be wrapped in `<b>...</b>`.
- `Audio` is optional. Leave the field empty if no audio is available; templates use conditional rendering `{{#Audio}}...{{/Audio}}`.
- Do not reuse `VocabID` values. Increment sequentially using the file's namespace (e.g., `001_0001`, `001_0002`).
- To delete a Note: add the tag `REPO_DELETE` to its tags column, re-import the CSV into Anki, search for `tag:REPO_DELETE` in Anki and manually delete those notes, then remove the row from the CSV.
