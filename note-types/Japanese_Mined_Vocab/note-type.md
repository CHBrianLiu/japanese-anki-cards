# Note Type: Japanese_Mined_Vocab

## Overview

This Note Type is designed for sentence-mining Japanese vocabulary. Each Note captures a word discovered in context, along with the sentence it was mined from, enabling two complementary Card Types: reading comprehension and active recall (production).

---

## Target Deck

Entry YAML's `deck` value is authoritative for API Card placement. Current entries
target `Japanese::Vocabulary` and `Japanese::Tadoku::<title>` Decks.

---

## ID Strategy

**User-defined unique identifier in the first field (`VocabID`) using a namespaced index.**

- Each entry YAML file must be prefixed with a 3-digit index (e.g., `001_明日は遠足.yaml`).
- Each Note must have a stable ID following the format `{FileIndex}_{Sequence}` (e.g., `001_0001`, `001_0152`).
- When importing the generated CSV with "Update existing notes where first field matches", Anki will match on `VocabID` to update existing Notes rather than creating duplicates.
- Direct YAML API import matches by Note Type plus the exact `VocabID` value.
- Never leave `VocabID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name            | Purpose                                                                                     |
|---|-----------------------|---------------------------------------------------------------------------------------------|
| 1 | `VocabID`             | Unique stable identifier for idempotent imports (e.g., `001_0152`).                         |
| 2 | `TargetWord`          | Dictionary form of the vocabulary word (e.g., `始まる`).                                   |
| 3 | `Reading`             | Kana reading or furigana (e.g., `はじまる`).                                                |
| 4 | `Meaning`             | Definition in the learner's native language (e.g., `to begin; to start`).                  |
| 5 | `Sentence`            | The mined Japanese sentence. The conjugated target word must be wrapped in `<b>` tags (e.g., `もう一時間めが<b>始まっています</b>。`). |
| 6 | `SentenceTranslation` | Full translation of the mined sentence into the learner's native language.                  |
| 7 | `Notes`               | Grammar nuances, kanji breakdowns, transitive/intransitive pairs, usage notes, etc.        |

### Native tags metadata

`Tags` in entry YAML is native Note metadata, **not an eighth ordinary Field**.
It replaces the managed Note's complete tag set; absent, null, or empty values
mean no tags. `REPO_DELETE` remains a manual-deletion workflow marker, not an
instruction to delete a Note automatically. Templates can use the native special
field `{{Tags}}`.

The legacy CSV configuration retains `Tags` as column 8, mapped by
`#tags column:8`. Its `fields` list describes that legacy import column layout;
only columns 1–7 correspond to ordinary Anki Fields.

---

## Card Types

1. **Comprehension** — Read the sentence in context; recognize and understand the bolded target word.
2. **Production** — Given the sentence with the target word blanked out and a native-language hint, recall the correct Japanese word.

Use the Front and Back Templates under each `card-types/` directory and the
shared Note Type stylesheet `style.css` for both Card Types. Production-specific
rules are scoped to its Template's `production` class, independent of order.

---

## Data Entry Rules

- Entry content is authored in `entries/*.yaml`. The sibling `entries-config.yaml` defines the canonical Field order used when generating the import CSV.
- The conjugated form of the target word in `Sentence` must always be wrapped in `<b>...</b>`.
- `Tags` is optional native metadata. Use it for Anki tags and repository workflow markers.
- Do not reuse `VocabID` values. Increment sequentially using the file's namespace (e.g., `001_0001`, `001_0002`).
- `VocabID` values must be quoted strings in YAML, for example `VocabID: "001_0001"`.
- After editing an entry YAML file, regenerate the corresponding CSV with `tools/yaml_to_csv/.venv/bin/python tools/yaml_to_csv/yaml_to_csv.py --file note-types/Japanese_Mined_Vocab/entries/<file>.yaml` or omit `--file` to regenerate all CSVs.
- To delete a Note through the existing CSV workflow: add `REPO_DELETE` to the Note's `Tags` metadata in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.

### Sandbox API exploration

`tools/headless_import/import_yaml.py` reads this Note Type's YAML directly and
imports its schema, Templates, shared CSS, and Notes into an explicitly selected
tool-created sandbox. It creates missing Decks through Anki's API and generates
no CSV. This sandbox-only exploration is not the guarded production workflow;
repository-wide retirement of mandatory CSV regeneration remains a later step.
