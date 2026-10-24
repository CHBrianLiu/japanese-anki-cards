# Card Type: Production

## Learning Intention

Produce a full Japanese sentence from an English prompt, then compare it with a
reference translation. Grade recall manually; differences in phrasing, kanji,
or punctuation are not automatically marked wrong.

## Field Mappings

- `{{SentenceID}}`: hidden identity used to guard temporary response retrieval.
- `{{EnglishSentence}}`: visible prompt on both sides.
- `{{JapaneseSentence}}`: reference answer on the back only.
- `{{Notes}}`: optional back-only explanations or alternative translations.
- `{{#Notes}}...{{/Notes}}`: omit the Notes section when the Field is empty.
- Native tags (`{{Tags}}`) are not displayed.

The Back Template intentionally does not include `{{FrontSide}}`: re-running the
Front Template would clear the typed response. Neither side uses Anki's `type:`
filter, which would generate an exact-match comparison rather than show the
learner's sentence unchanged.

## Input and Temporary State

The front uses an explicitly labelled Japanese textarea. It supports wrapping and
multiple lines without an Enter-to-reveal shortcut, allowing Japanese IME
composition and candidate confirmation. Tap the input to open the mobile keyboard,
and use the client's normal Show Answer control when ready.

Every front render resets the response, including repeated reviews of the same
Note. Input, composition-end, and change events save the response to a namespaced
review-page property and browser `localStorage`. The latter allows retrieval when
a client replaces the page between the front and back. Storage access is guarded
because some client contexts may not allow it. If the page is replaced and storage
is unavailable, the back explicitly reports that retrieval failed.

The back checks both the Note ID and English prompt before displaying a response.
It uses `textContent`, not HTML insertion, preserving whitespace and displaying
typed markup literally. An empty response is labelled "No answer entered."

Responses are not saved to Notes or synced between devices. Browser storage holds
only the latest response for this Note Type until its next front render overwrites
it (or the client's browser storage is cleared). It is not an answer history.

## Styling

Per-Card-Type styling follows the repository's existing Japanese sans-serif fonts,
640px content width, and neutral light background. The prompt, typed response, and
reference answer have clear labels; no comparison colors imply an automatic grade.
The input is full-width with a visible focus outline, and light and night modes
have explicit text, input, and border colors.

## Verification

Run `node tools/test_sentence_production.cjs` for simulated front-to-back state
tests. These are not a substitute for real client tests. Anki does not guarantee
JavaScript Template behavior across clients or versions.

Before relying on this Card Type, review the sample Note in Anki desktop,
AnkiMobile (iOS), and AnkiDroid (Android), checking:

- Japanese IME candidate confirmation, punctuation, and multiline input.
- Revealing the answer preserves the response exactly and hides the input.
- An unanswered review shows "No answer entered." rather than stale content.
- Consecutive Notes and repeated reviews reset the input.
- Mobile keyboard behavior, small screens, and night mode remain usable.

CSV import only imports Notes; it does not install the Note Type or its Templates.
