# Note Type: Spanish_Survival_Phrase

## Overview

This Note Type is designed for Spanish travel-survival phrase mining with production-first review. Each Note captures a single phrase mined from video material that the learner wants to be able to say out loud in Latin America, with optional attached audio for post-recall feedback.

---

## Target Deck

`Spanish::Travel::Survival`

---

## ID Strategy

**User-defined unique identifier in the first field (`PhraseID`) using a namespaced index.**

- Each entry YAML file must be prefixed with a 3-digit index (e.g. `001_restaurants.yaml`).
- Each Note must have a stable ID following the format `{FileIndex}_{Sequence}` (e.g. `001_0001`, `001_0152`).
- When importing the generated CSV with "Update existing notes where first field matches", Anki will match on `PhraseID` to update existing Notes rather than creating duplicates.
- Never leave `PhraseID` empty. Never reuse or reassign an ID once created.

---

## Fields

| # | Field Name | Purpose |
|---|---|---|
| 1 | `PhraseID` | Unique stable identifier for idempotent imports (e.g. `001_0001`). |
| 2 | `EnglishPrompt` | Natural English prompt for what the learner wants to say (e.g. `Can I have the bill, please?`). |
| 3 | `Situation` | Short disambiguating cue such as `restaurant`, `asking directions`, or `polite request`. |
| 4 | `SpanishPhrase` | The Spanish phrase to actively recall and say out loud. |
| 5 | `Audio` | Optional Anki audio markup such as `[sound:spa_001_0001.mp3]`. |
| 6 | `Notes` | Optional usage notes, politeness level, regional nuance, or alternate phrasing reminders. |
| 7 | `Tags` | Optional Anki tags for organization, workflow markers, or deletion tagging such as `REPO_DELETE`. |

---

## Card Types

1. **Production** — Given an English prompt and a short situational cue, actively recall the Spanish phrase, then check the answer and play the audio.

---

## Data Entry Rules

- Entry content is authored in `entries/*.yaml`. The sibling `entries-config.yaml` defines the canonical Field order used when generating the import CSV.
- `EnglishPrompt` should be phrased as the communicative intention the learner wants to express, not as a grammar label.
- `Situation` should stay short and scannable. Treat it as a disambiguating cue, not a paragraph.
- `SpanishPhrase` should be the exact phrase being tested on the Card. Since this Note Type is for mined video material, prefer phrases that are short enough to be realistically recallable and reusable during travel.
- `Audio` is optional. When present, store it using standard Anki sound markup such as `[sound:spa_001_0001.mp3]`.
- `Notes` is optional. Use it for politeness guidance, regional caveats for Latin America, or reminders about when not to use a phrase.
- `Tags` is optional. Use it for Anki tags and repository workflow markers.
- `PhraseID` values must be quoted strings in YAML, for example `PhraseID: "001_0001"`.
- After editing an entry YAML file, regenerate the corresponding CSV with `python tools/yaml_to_csv.py --file note-types/Spanish_Survival_Phrase/entries/<file>.yaml` or regenerate all CSVs with `python tools/yaml_to_csv.py`.
- To delete a Note: add the tag `REPO_DELETE` to the Note's `Tags` Field in YAML, regenerate the CSV, import it into Anki, search for `tag:REPO_DELETE`, manually delete the matching Notes, then remove the YAML entry and regenerate the CSV again.
