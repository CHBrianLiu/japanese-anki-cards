# Note Type: Japanese_Familiarity_Vocab

## Overview

This Note Type is designed for reviewing list-based Japanese vocabulary with low recall pressure.
Its purpose is to remind you of words you have encountered before and help you notice whether a word feels known, half-known, or unfamiliar.

It does **not** assume you are trying to memorize new words from the list.
Instead, it supports proficiency-list entries (such as JLPT word lists) where translations may be sparse or missing.

---

## Target Decks

- `Japanese::JLPT::N5`
- `Japanese::JLPT::N4`
- Other proficiency-list or textbook-list decks as needed.

When creating an entry YAML file, place the target deck in the `deck` key.
The deck name may differ from the source list name and does not have to match a schema-level target deck.

---

## ID Strategy

**User-defined unique identifier in the first field (`WordID`) using a namespaced index.**

- Each entry YAML file must be prefixed with a 3-digit index (e.g. `005_JLPT_N5.yaml`).
- Each Note must have a stable ID following the format `{FileIndex}_{Sequence}` (e.g. `005_0001`, `005_0152`).
- When importing the generated CSV with **Update existing notes where first field matches**, Anki will match on `WordID` to update existing Notes rather than creating duplicates.
- Never leave `WordID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name     | Required | Purpose                                                                                              |
|---|----------------|----------|------------------------------------------------------------------------------------------------------|
| 1 | `WordID`       | Yes      | Unique stable identifier for idempotent imports (e.g. `005_0001`).                                   |
| 2 | `DisplayWord`  | Yes      | Clean learner-facing Japanese form shown on the Front template (e.g. `回`, `お酒`, `タバコ`).         |
| 3 | `Reading`      | No       | Kana reading (e.g. `かい`, `おさけ`). Leave empty when `DisplayWord` is already kana-only.            |
| 4 | `Meaning`      | No       | Native-language definition when available (e.g. `times; counter` or `sake`). May be left empty.       |
| 5 | `UsageLabel`   | No       | Short classifier or role label (e.g. `助数詞`, `敬称`, `比較`) shown as a visual badge on the back.    |
| 6 | `Example`      | No       | Optional example sentence for context. Not required for every entry.                                  |
| 7 | `Source`       | No       | Source list name (e.g. `JLPT N5`) shown as a compact badge on the back.                               |
| 8 | `Notes`        | No       | Additional context, abbreviation notes, or reminders about source-form quirks.                        |
| 9 | `Tags`         | No       | Optional Anki tags for organization, workflow markers, or deletion tagging such as `REPO_DELETE`.     |

---

## Card Types

1. **Familiarity (single Card Type)**
   - **Front**: Displays only `DisplayWord`. You self-assess whether you recognize the word.
   - **Back**: Reveals `Reading`, `Meaning`, `UsageLabel`, and `Example` (if present), plus optional `Notes`. Keeps review light and reminder-oriented.

---

## Normalization Rules for List Entries

When importing from a proficiency-list source, apply light normalization to produce clean review forms:

- Strip source-specific shorthand such as `・・・` prefixes.
- Convert han-dakuten variants to standard forms (e.g. `ぴき` stays `ひき` when `DisplayWord` is `匹`).
- Remove optional-kana parentheses in the main word (e.g. `（お）さけ` -> `お酒`).
- Move extracted role labels into `UsageLabel` (e.g. `助数詞`, `敬称`).
- Move mixed script / variant notes into `Notes` when they would clutter the main review form.
- The `DisplayWord` is the word you actually review; the original list form is preserved only in `Notes` if it differs materially.

---

## Data Entry Rules

- Entry content is authored in `entries/*.yaml`. The sibling `entries-config.yaml` defines the canonical Field order used when generating the import CSV.
- `DisplayWord` must never be empty.
- `Reading` may be left empty when the word is already written in kana and no additional reading is needed.
- `Meaning` may be left empty when translations are unavailable.
- `Tags` is optional. Use it for Anki tags and repository workflow markers.
- `WordID` values must be quoted strings in YAML, for example `WordID: "005_0001"`.
- After editing an entry YAML file, regenerate the corresponding CSV with `python tools/yaml_to_csv.py --file note-types/Japanese_Familiarity_Vocab/entries/<file>.yaml` or regenerate all CSVs with `python tools/yaml_to_csv.py`.
- To delete a Note: add the tag `REPO_DELETE` to the Note's `Tags` Field in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.
