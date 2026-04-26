# Card Type: Comprehension

**Parent Note Type:** `Japanese_Mined_Grammar`

---

## Learning Intention

Test whether the learner can read the mined sentence in context, recognize the highlighted grammar span, and understand the specific nuance and formation being tested. This is a passive recognition Card: the stimulus is the Japanese sentence, and the expected output is comprehension of the grammar point in that sentence.

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---|---|---|
| Sentence | `{{Sentence}}` | Rendered as HTML. The `<b>` tag in the data highlights the full tested grammar span directly in the sentence. |

The front is intentionally minimal so the learner first reads the sentence naturally.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---|---|---|
| Sentence (repeated) | `{{Sentence}}` | Shown again at the top for context continuity. |
| Grammar point | `{{GrammarPoint}}` | Canonical label for the grammar concept being tested. |
| Meaning | `{{Meaning_Hint}}` | Sentence-specific nuance shown as the primary explanation. |
| Formation | `{{Formation}}` | Concise formation rule shown as a second reference line. |
| Translation (collapsible) | `{{SentenceTranslation}}` | Native `<details>`/`<summary>` block. Collapsed by default. |
| Notes (collapsible) | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Only shown if the field is non-empty. |

---

## Conditional Logic

- `{{#Notes}}...{{/Notes}}` — The Notes collapsible is only rendered if `Notes` is non-empty.
- `{{SentenceTranslation}}` is always shown (not conditional), as a translation is expected for every Note.

---

## Styling Notes (`style.css`)

- Japanese font stack: `"Hiragino Sans"`, `"Yu Gothic"`, `"Noto Sans JP"`.
- The bolded grammar span in the sentence is colored `#1a6ebd` to anchor the learner's attention.
- The answer area is split into compact labeled rows so `GrammarPoint`, `Meaning_Hint`, and `Formation` are easy to scan separately.
- Collapsible blocks use native `<details>`/`<summary>` HTML — no JavaScript required.
- Styling is scoped to this Card Type; no global stylesheet is assumed.
