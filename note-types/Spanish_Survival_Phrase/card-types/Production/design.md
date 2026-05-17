# Card Type: Production

**Parent Note Type:** `Spanish_Survival_Phrase`

---

## Learning Intention

Test whether the learner can actively produce a travel-useful Spanish phrase from an English communicative prompt. This Card Type is designed for speaking-first review: the learner sees what they want to say, uses the situational cue to disambiguate it, says the Spanish phrase out loud, then flips to check the answer and optionally replay the mined audio.

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---|---|---|
| English prompt | `{{EnglishPrompt}}` | Main cue for active recall. This should read like a real intention the learner wants to express. |
| Situational cue | `{{Situation}}` | Short contextual cue shown as a pill to reduce ambiguity without overloading the front. |
| Speaking reminder | — | Static text reminding the learner to answer out loud before revealing the back. |

The front is intentionally minimal. It avoids showing Spanish or audio so the review stays production-focused.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---|---|---|
| English prompt (repeated) | `{{EnglishPrompt}}` | Repeated for context continuity. |
| Situational cue (repeated) | `{{Situation}}` | Repeated so the learner sees the exact prompt again while checking the answer. |
| Answer label | — | Static `Spanish` label above the target phrase. |
| Spanish phrase | `{{SpanishPhrase}}` | Main answer reveal. Displayed prominently. |
| Audio block | `{{Audio}}` | Conditional: `{{#Audio}}...{{/Audio}}`. Only shown when a mined clip is available. |
| Notes block | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Use for usage notes, politeness, or Latin America-specific nuance. |

---

## Conditional Logic

- `{{#Audio}}...{{/Audio}}` — The audio block is rendered only if `Audio` is non-empty.
- `{{#Notes}}...{{/Notes}}` — The Notes block is rendered only if `Notes` is non-empty.
- No other conditional logic or JavaScript is used.

---

## Styling Notes (`style.css`)

- The visual language is warm and travel-oriented rather than matching the Japanese card styling exactly.
- `EnglishPrompt` is large and central because it is the primary cue for recall.
- `Situation` is styled as a compact uppercase pill so it helps disambiguation without competing with the prompt.
- `SpanishPhrase` is the strongest visual element on the back to make answer checking immediate.
- The audio block is visually separated so playback feels like feedback, not part of the prompt.
- Styling is scoped to this Card Type; no global stylesheet is assumed.
