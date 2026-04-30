# Note Type: Spanish_Travel_Phrases

## Overview

This Note Type is designed for simple Spanish travel phrases. Each Note captures a short phrase, a learner-friendly pronunciation guide, and a plain English cue for fast cramming.

---

## Target Deck

`Spanish::Travel`

---

## ID Strategy

**User-defined unique identifier in the first field (`PhraseID`) using a namespaced index.**

- Each entry YAML file should use a stable prefix such as `001_0001`, `001_0002`, and so on.
- When importing the generated CSV with "Update existing notes where first field matches", Anki will match on `PhraseID` to update existing Notes rather than creating duplicates.
- Never leave `PhraseID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name | Purpose |
|---|---|---|
| 1 | `PhraseID` | Unique stable identifier for idempotent imports, such as `001_0001`. |
| 2 | `Spanish` | The Spanish phrase the learner should recall. |
| 3 | `Pronunciation` | A learner-friendly pronunciation guide. |
| 4 | `English` | The English meaning prompt shown on the front of the Card. |
| 5 | `Category` | Optional topic label such as `Greetings & Basics`. |
| 6 | `Notes` | Optional usage note, formality note, or reminder. |
| 7 | `Tags` | Optional Anki tags for organization, workflow markers, or deletion tagging such as `REPO_DELETE`. |

---

## Card Types

1. **Production** - Given an English travel prompt, recall the Spanish phrase.

---

## Data Entry Rules

- Entry content is authored in `entries/*.yaml`. The sibling `entries-config.yaml` defines the canonical Field order used when generating the import CSV.
- `PhraseID` values must be quoted strings in YAML, for example `PhraseID: "001_0001"`.
- Keep entries minimal. If a field is not needed, leave it empty or omit it where allowed.
- `Category` should be used to group phrases by topic when helpful.
- `Tags` is optional. Use it for Anki tags and repository workflow markers.
- After editing an entry YAML file, regenerate the corresponding CSV with `python tools/yaml_to_csv.py --file note-types/Spanish_Travel_Phrases/entries/<file>.yaml` or regenerate all CSVs with `python tools/yaml_to_csv.py`.
- To delete a Note: add the tag `REPO_DELETE` to the Note's `Tags` Field in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.
