# Note Type: Japanese_Listening

## Overview

Practice understanding spoken Japanese before seeing its written form. Each Note
contains one short recorded utterance and its matching Japanese transcript. This
Note Type generates one meaning-first listening Card; it does not test dictation
or require an English translation.

Start with clear recordings, roughly 3–10 seconds long, whose vocabulary and
grammar you already understand in writing. Preserve spoken contractions in the
transcript and choose utterances that make sense without unseen context.

## Target Deck

`Japanese::Listening`

## ID Strategy

User-defined stable identifier in the first Field, `ListeningID`.

- Prefix entry filenames with a three-digit file index, such as `001_practice.yaml`.
- Use `{FileIndex}_{Sequence}` IDs, such as `001_0001`. Never reuse or reassign IDs.
- IDs must be nonempty, quoted YAML strings: `ListeningID: "001_0001"`.
- Import generated CSV files with **Update existing notes where first field matches**.
  Anki matches `ListeningID` to update existing Notes instead of creating duplicates.

## Fields

| # | Field Name | Purpose |
|---|---|---|
| 1 | `ListeningID` | Required stable identifier for repeatable imports. |
| 2 | `Audio` | Required recording reference, such as `[sound:japanese_listening__001_0001__audio.mp3]`. |
| 3 | `JapaneseSentence` | Required Japanese transcript matching the recording; back only. |
| 4 | `Reading` | Optional kana reading aid for the transcript; back only. |
| 5 | `Notes` | Optional Japanese explanations of meaning, vocabulary, grammar, or connected speech; back only. |
| 6 | `Source` | Optional attribution, episode, timestamp, or source URL; back only. |
| 7 | `Tags` | Optional import column mapped to Anki's native tags, not a custom Anki Field. |

Create the first six Fields in Anki in this order. The repository's seventh column,
`Tags`, is mapped to native tags by the generated `#tags column:7` header. Templates
would use `{{Tags}}` to display native tags; this Card Type does not display them.
There is no English translation Field.

## Card Types

1. **ListeningComprehension**: Audio and a listening instruction on the front;
   audio, Japanese transcript, and optional reading aid, Notes, and source on the back.
   The Front Template is conditional on `Audio` so Notes without audio do not
   generate this Card.

## Setup and Data Entry

1. Create the `Japanese_Listening` Note Type in Anki with the six Fields above and
   a single `ListeningComprehension` Card Type. Use the Front and Back Templates
   under `card-types/ListeningComprehension/` and the shared Note Type stylesheet
   `style.css` for Styling.
2. Author Notes in `entries/*.yaml`, using the Field order in `entries-config.yaml`.
   Each entry file must declare `notetype: Japanese_Listening`, a `deck` such as
   `Japanese::Listening`, and at least one Note under `entries`.
3. Store recordings in the project-root `media/` directory using
   `japanese_listening__{note-id}__audio.mp3` (or the actual audio extension).
   Store the full `[sound:filename]` reference in `Audio`, with only the basename
   and no `media/` path. Do not build sound references from filenames in Templates.
4. Regenerate the CSV after every entry edit:
   `tools/yaml_to_csv/.venv/bin/python tools/yaml_to_csv/yaml_to_csv.py --file note-types/Japanese_Listening/entries/001_practice.yaml`.
   The generated CSV includes `#notetype:Japanese_Listening`, the entry file's
   `#deck`, `#separator:Comma`, `#html:true`, and `#tags column:7` headers, followed
   by the seven configured columns. Do not hand-edit the CSV.
5. Copy the recordings directly into the Anki profile's `collection.media` folder,
   preserving their filenames and using no subfolders. On macOS, the default path
   is `~/Library/Application Support/Anki2/<ProfileName>/collection.media/`.
   CSV import references these files; it does not copy them.
6. Import the CSV via **File → Import**, allowing HTML and updating Notes where the
   first Field matches. Map the seventh column to native tags.
7. Run **Tools → Check Media**, test audio playback, and sync with audio/image
   synchronization enabled to make recordings available on other devices.

This directory initially contains configuration only: no actual Notes, recordings,
or generated CSV files are included.

To delete a Note, first add `REPO_DELETE` to its `Tags` value, regenerate and import,
then search for `tag:REPO_DELETE` and manually delete the matching Notes in Anki.
Only after that cleanup should you remove the YAML entry and regenerate again.

## Review and Grading

Listen and understand the utterance before revealing the answer. No typing or
exact translation is required. On the back, use the transcript to identify missed
sounds and listen again while following the text.

- **Again:** Missed or misunderstood the core meaning.
- **Hard:** Understood only after several listens or substantial effort.
- **Good:** Understood the core meaning, allowing minor missed details.
- **Easy:** Understood immediately and comfortably.

Grade comprehension before revealing the transcript, not recognition afterward.
If the meaning remains unclear after reading, clarify it and optionally record a
Japanese explanation in `Notes` before continuing reviews.
