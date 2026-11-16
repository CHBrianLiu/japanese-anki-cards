# Note Type: Japanese_Mined_Grammar

## Overview

This Note Type is designed for sentence-mined Japanese grammar. Each Note captures a single grammar point in a real sentence, with the tested span marked directly in the sentence so the learner reviews both recognition and active recall in context.

---

## Target Deck

Entry YAML's `deck` value is authoritative for API Card placement. Current entries
target `Japanese::Tadoku::<title>` Decks; `Japanese::Grammar` is intended context,
not an override of entry declarations.

---

## ID Strategy

**User-defined unique identifier in the first field (`GrammarID`) using a namespaced index.**

- Each entry YAML file must be prefixed with a 3-digit index (e.g. `001_明日は遠足.yaml`).
- Each Note must have a stable ID following the format `{FileIndex}_{Sequence}` (e.g. `001_0001`, `001_0152`).
- When importing the generated CSV with "Update existing notes where first field matches", Anki will match on `GrammarID` to update existing Notes rather than creating duplicates.
- Never leave `GrammarID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name | Purpose |
|---|---|---|
| 1 | `GrammarID` | Unique stable identifier for idempotent imports (e.g. `001_0001`). |
| 2 | `GrammarPoint` | Canonical label for the grammar concept being tested (e.g. `と`). |
| 3 | `Meaning_Hint` | Sentence-specific nuance or meaning prompt shown on review cards. |
| 4 | `Formation` | Concise formation rule for the grammar point (e.g. `Verb (Dictionary Form) + と`). |
| 5 | `Sentence` | The mined Japanese sentence, with the full tested answer span wrapped in `<b>...</b>` (e.g. `教室に<b>入ると</b>先生がレオ君に言いました。`). |
| 6 | `SentenceTranslation` | Full translation of the mined sentence into the learner's native language. |
| 7 | `Notes` | Optional usage notes, source context, restrictions, contrasts, or reminders. |

### Native tags metadata

Entry YAML `Tags` is native Note metadata, not an eighth ordinary Field. API
import replaces the complete tag set; absent, null, or empty values clear it.
`REPO_DELETE` remains a manual-deletion marker. Templates can use `{{Tags}}`.
The unchanged legacy config retains `Tags` as CSV column 8, mapped by
`#tags column:8`; only its first seven columns are ordinary Anki Fields.

---

## Card Types

1. **Comprehension** — Read the sentence in context, recognize the highlighted grammar span, and recall the grammar point, nuance, and formation.
2. **Production** — Given the sentence with the tested span blanked out and a meaning hint, actively recall the full grammar chunk in context.

Use the Front and Back Templates under each `card-types/` directory and the
shared Note Type stylesheet `style.css` for both Card Types. Production-specific
rules are scoped to its Template's `production` class, independent of order.

---

## Data Entry Rules

- Entry content is authored in `entries/*.yaml`. The sibling `entries-config.yaml` defines the canonical Field order used when generating the import CSV.
- The `Sentence` field must always wrap the full tested answer span in `<b>...</b>`, not only the abstract grammar label. For example, use `教室に<b>入ると</b>...`, not `教室に入る<b>と</b>...` if the Card Type is meant to test both formation and the grammar point.
- `Meaning_Hint` should describe the nuance being tested in the specific sentence, not only a dictionary-style gloss of the grammar point.
- `Formation` should be short and mechanical so it is easy to scan on the back of a Card.
- `SentenceTranslation` is required for every Note.
- `Notes` is optional. Leave it empty if there is nothing worth calling out.
- `Tags` is optional. Use it for Anki tags and repository workflow markers.
- `GrammarID` values must be quoted strings in YAML, for example `GrammarID: "001_0001"`.
- After editing an entry YAML file, regenerate the corresponding CSV with `tools/yaml_to_csv/.venv/bin/python tools/yaml_to_csv/yaml_to_csv.py --file note-types/Japanese_Mined_Grammar/entries/<file>.yaml` or omit `--file` to regenerate all CSVs.
- To delete a Note: add the tag `REPO_DELETE` to the Note's `Tags` metadata in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.
