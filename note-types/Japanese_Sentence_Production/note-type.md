# Note Type: Japanese_Sentence_Production

## Overview

Practice producing a Japanese sentence from an English prompt. The learner types
a response, reveals the reference answer, and grades their own recall. Alternative
valid translations are welcome; there is no automatic grading or exact-match check.

## Target Deck

`Japanese::Sentence Production`

Source-specific subdecks:

- `Japanese::Sentence Production::出口日語N4文法` — grammar examples from
  `出口日語N4文法.md`, authored in `entries/002_deguchi_n4_grammar.yaml`.
- `Japanese::Sentence Production::布団の中から出たくない` — sentences mined from
  the song `布団の中から出たくない`, authored in `entries/003_futon_song.yaml`.

## ID Strategy

User-defined stable identifier in the first Field, `SentenceID`.

- Prefix entry filenames with a three-digit file index, such as `001_practice.yaml`.
- Use `{FileIndex}_{Sequence}` IDs, such as `001_0001`. Never reuse or reassign IDs.
- IDs must be nonempty, quoted YAML strings: `SentenceID: "001_0001"`.
- Import generated CSV files with **Update existing notes where first field matches**.
  Anki matches `SentenceID` to update existing Notes instead of creating duplicates.

## Fields

| # | Field Name | Purpose |
|---|---|---|
| 1 | `SentenceID` | Required stable identifier for repeatable imports. |
| 2 | `EnglishSentence` | Required English sentence shown as the production prompt. |
| 3 | `JapaneseSentence` | Required reference Japanese sentence, revealed on the back. |
| 4 | `Notes` | Optional explanations or alternative translations, shown only on the back. |
| 5 | `Tags` | Optional import column mapped to Anki's native tags, not a custom Anki Field. |

Create the first four Fields in Anki in this order. The repository's fifth column,
`Tags`, is mapped to native tags by the generated `#tags column:5` header. Templates
would use `{{Tags}}` to display native tags; this Card Type does not display them.

## Card Types

1. **Production**: English prompt and Japanese text input on the front; English
   prompt, unchanged typed response, reference answer, and optional Notes on the back.

## Setup and Data Entry

1. Create this Note Type in Anki with the Fields above and a single `Production`
   Card Type. Replace its Front Template, Back Template, and Styling with the
   corresponding files under `card-types/Production/`.
2. Author Notes in `entries/*.yaml`, using the Field order in `entries-config.yaml`.
3. Regenerate the CSV after every entry edit:
   `tools/.venv/bin/python tools/yaml_to_csv.py --file note-types/Japanese_Sentence_Production/entries/001_practice.yaml`.
4. Import the generated CSV via **File -> Import**, updating Notes where the first
   Field matches. A convenient generated symlink is also available under root `entries/`.

To delete a Note, first add `REPO_DELETE` to its `Tags` value, regenerate and import,
then search for `tag:REPO_DELETE` and manually delete the matching Notes in Anki.
Only after that cleanup should you remove the YAML entry and regenerate again.

Typed responses are temporary review state, not Note Fields. See the Card Type's
`design.md` for storage behavior and cross-client testing requirements.
