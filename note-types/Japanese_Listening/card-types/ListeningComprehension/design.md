# Card Type: ListeningComprehension

**Parent Note Type:** `Japanese_Listening`

## Learning Intention

Understand the core meaning of a short spoken Japanese utterance without first
seeing its transcript. This is listening comprehension, not dictation, reading
comprehension, or exact translation recall. The learner thinks of the meaning,
reveals the answer, and grades comprehension before the reveal.

## Front Template

**File:** `front.html`

| Element | Field | Behavior |
|---|---|---|
| Recording | `{{Audio}}` | Full Anki sound reference stored in the Field; native playback and replay control. |
| Instruction | None | Static text: “Listen and understand.” |

The whole front is wrapped in `{{#Audio}}...{{/Audio}}`. Without `Audio`, the
rendered front is empty and Anki does not generate this Card for a new Note.
Entry validation also requires `Audio` and `JapaneseSentence` to be nonempty.
If audio is cleared from an existing Note in Anki, use Anki's Empty Cards tool
to handle the existing Card; the conditional does not delete it automatically.

No transcript, reading aid, Notes, source, ID, tags, translation, or image appears
on the front. No typed response, JavaScript, or custom audio player is used.

## Back Template

**File:** `back.html`

| Element | Field | Behavior |
|---|---|---|
| Recording | `{{Audio}}` | Included directly once for native replay and automatic playback when enabled. |
| Transcript | `{{JapaneseSentence}}` | Always visible; the Japanese text must match the recording. |
| Reading aid | `{{Reading}}` | Optional, collapsed by default. |
| Explanation | `{{Notes}}` | Optional Japanese explanation, collapsed by default. |
| Attribution | `{{Source}}` | Optional source information, collapsed by default. |

The back does not use `{{FrontSide}}`: it includes `{{Audio}}` directly because
Anki does not automatically replay front audio through `{{FrontSide}}`. The
recording can therefore play again while the learner reads the transcript.
Anki's **Don't play audio automatically** Deck option controls automatic
playback; native replay remains available when automatic playback is disabled.
Replay buttons must be enabled in the client's preferences to remain visible.

Source URLs are ordinary Field content. Use an HTML link in `Source` if a clickable
link is wanted; Templates do not construct links or media filenames dynamically.

## Conditional Logic

- `{{#Audio}}...{{/Audio}}`: gates the entire Front Template.
- `{{#Reading}}...{{/Reading}}`: shows the Reading collapsible only when populated.
- `{{#Notes}}...{{/Notes}}`: shows the Notes collapsible only when populated.
- `{{#Source}}...{{/Source}}`: shows the Source collapsible only when populated.
- Optional sections use native `<details>` and `<summary>` elements; they start
  collapsed on each rendering and require no saved review state.

All referenced Fields are declared in the parent `note-type.md`. `Tags` is a
repository import column mapped to native Anki tags, not a custom Field, and is
not displayed by this Card Type.

## Styling

**File:** `../../style.css` (shared by the Note Type)

- Styling is shared by all Card Types of this Note Type.
- Japanese font stack: `"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`.
- Centered audio and transcript with a 640px maximum content width.
- Optional content uses separate bordered collapsibles.
- Support for `.nightMode` and `.night_mode`, narrow screens, and long source URLs.
- Native audio replay controls are left intact for client compatibility.

## Grading

- **Again:** Missed or misunderstood the core meaning.
- **Hard:** Understood only after several listens or substantial effort.
- **Good:** Understood the core meaning, allowing minor missed details.
- **Easy:** Understood immediately and comfortably.

The transcript checks what was heard; it is not a required exact-match answer.
If the meaning remains unclear after reading, clarify it before continuing reviews.
Prefer material already understandable in writing so listening is the main challenge.

## Validation and Client Checks

Before reviewing real Notes, verify on each Anki client you use:

1. With a valid recording, the front plays audio when automatic playback is enabled
   and reveals no answer text. Native replay works with autoplay enabled or disabled.
2. Revealing the back shows the transcript and plays the recording again when
   automatic playback is enabled, without duplicate audio controls.
3. Empty optional Fields leave no headings or blank collapsibles; populated ones
   expand correctly. Japanese text, source links, dark mode, and narrow layouts work.
4. A new Note without `Audio` generates no Card. Repository entry validation rejects
   missing audio, missing transcript, and empty or non-string IDs.
5. **Tools → Check Media** reports no missing recordings after copying the files
   into `collection.media`; media synchronization makes them playable elsewhere.

## References

- [Importing media](https://docs.ankiweb.net/importing/text-files.html#importing-media)
- [Special Fields and FrontSide audio behavior](https://docs.ankiweb.net/templates/fields.html#special-fields)
- [Deck audio options](https://docs.ankiweb.net/deck-options.html#audio)
