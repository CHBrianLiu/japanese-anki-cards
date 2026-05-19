# Card Type: Familiarity

**Parent Note Type:** `Japanese_Familiarity_Vocab`

---

## Learning Intention

Test whether you recognize and feel familiar with a Japanese word from a proficiency list.
This is a low-pressure reminder card: the stimulus is the Japanese word itself, and the expected output is a quick self-assessment of whether the word feels known, half-known, or unfamiliar.

This is not a memorization drill. It is designed for large vocabulary lists where you have encountered words before and simply want to be reminded of them.

---

## Front Template

**File:** `front.html`

| Element      | Field            | Notes                                                         |
|--------------|------------------|---------------------------------------------------------------|
| Display word | `{{DisplayWord}}`| Rendered prominently and centered. Nothing else is shown.    |

The front is intentionally minimal so you can focus on whether the word alone triggers recognition.

---

## Back Template

**File:** `back.html`

| Element          | Field              | Notes                                                              |
|------------------|--------------------|--------------------------------------------------------------------|
| Display word     | `{{DisplayWord}}`  | Shown again at the top for continuity.                             |
| Reading          | `{{Reading}}`      | Conditional: `{{#Reading}}...{{/Reading}}`. Kana reading if available. |
| Meaning          | `{{Meaning}}`      | Conditional: `{{#Meaning}}...{{/Meaning}}`. Definition if available. |
| Usage label      | `{{UsageLabel}}`   | Conditional badge (e.g. `助数詞`).                                 |
| Source           | `{{Source}}`       | Conditional badge (e.g. `JLPT N5`).                                |
| Example          | `{{Example}}`      | Conditional block with labeled example sentence.                   |
| Notes            | `{{Notes}}`        | Conditional collapsible block. Only shown if non-empty.            |

All optional fields are hidden when empty, so the back stays scannable and never feels cluttered.

---

## Conditional Logic

- `{{#Reading}}...{{/Reading}}` — Only shown if `Reading` is non-empty.
- `{{#Meaning}}...{{/Meaning}}` — Only shown if `Meaning` is non-empty.
- `{{#UsageLabel}}...{{/UsageLabel}}` — Only shown if `UsageLabel` is non-empty.
- `{{#Source}}...{{/Source}}` — Only shown if `Source` is non-empty.
- `{{#Example}}...{{/Example}}` — Only shown if `Example` is non-empty.
- `{{#Notes}}...{{/Notes}}` — The Notes collapsible is only rendered if `Notes` is non-empty.

---

## Styling Notes (`style.css`)

- Japanese font stack: `"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`.
- Calm neutral background (`#fcfcfc`) to reduce visual fatigue during bulk review.
- `DisplayWord` is large and centered.
- Badges for `UsageLabel` and `Source` use distinct pill styling with subtle color coding.
- `Example` block is visually separated with a light card-like container.
- Collapsible blocks use native `<details>`/`<summary>` HTML.
- Mobile-friendly spacing and font sizing.
- Styling is scoped to this Card Type; no global stylesheet is assumed.
