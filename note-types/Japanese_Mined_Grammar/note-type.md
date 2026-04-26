# Note Type: Japanese_Mined_Grammar

## Overview

This Note Type is designed for sentence-mined Japanese grammar. Each Note captures a single grammar point in a real sentence, with the tested span marked directly in the sentence so the learner reviews both recognition and active recall in context.

---

## Target Deck

`Japanese::Grammar`

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
| 8 | `Tags` | Optional Anki tags for organization, workflow markers, or deletion tagging such as `REPO_DELETE`. |

---

## Card Types

1. **Comprehension** — Read the sentence in context, recognize the highlighted grammar span, and recall the grammar point, nuance, and formation.
2. **Production** — Given the sentence with the tested span blanked out and a meaning hint, actively recall the full grammar chunk in context.

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
- After editing an entry YAML file, regenerate the corresponding CSV with `python tools/yaml_to_csv.py --file note-types/Japanese_Mined_Grammar/entries/<file>.yaml` or regenerate all CSVs with `python tools/yaml_to_csv.py`.
- To delete a Note: add the tag `REPO_DELETE` to the Note's `Tags` Field in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.
