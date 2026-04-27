# Card Type: Comprehension

**Parent Note Type:** `Japanese_Mined_Vocab`

---

## Learning Intention

Test whether the learner can read the mined sentence in context, recognize the bolded target word in its conjugated form, and understand its meaning. This is a passive recognition card: the stimulus is Japanese text, and the expected output is comprehension of the target vocabulary.

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---------|-------|-------|
| Sentence | `{{Sentence}}` | Rendered as HTML. The `<b>` tag in the data naturally bolds the conjugated target word, providing a visual focal point without additional JS. |

The front is intentionally minimal — the sentence alone is the stimulus.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---------|-------|-------|
| Sentence (repeated) | `{{Sentence}}` | Shown again at the top for context continuity. |
| Dictionary form | `{{TargetWord}}` | The base/dictionary form of the word. |
| Reading | `{{Reading}}` | Kana reading shown in parentheses next to the word. |
| Meaning | `{{Meaning}}` | Native-language definition on the same vocabulary line. |
| Translation (collapsible) | `{{SentenceTranslation}}` | Native `<details>`/`<summary>` block. Collapsed by default. |
| Notes (collapsible) | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Only shown if the field is non-empty. Native `<details>`/`<summary>` block. Collapsed by default. |

---

## Conditional Logic

- `{{#Notes}}...{{/Notes}}` — The Notes collapsible is only rendered if `Notes` is non-empty.
- `{{SentenceTranslation}}` is always shown (not conditional), as a translation is expected for every note.

---

## Styling Notes (`style.css`)

- Japanese font stack: `"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`.
- The bolded target word in the sentence is colored `#1a6ebd` (blue) to draw the eye.
- Collapsible blocks use native `<details>`/`<summary>` HTML — no JavaScript required.
- Custom `::before` pseudo-element replaces the default browser disclosure triangle with `▶` / `▼`.
- Styling is scoped to this Card Type; no global stylesheet is assumed.
