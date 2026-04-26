# Card Type: Production

**Parent Note Type:** `Japanese_Mined_Grammar`

---

## Learning Intention

Test whether the learner can actively recall the correct grammar chunk given sentence context and a meaning hint. This is an active recall Card: the stimulus is a gapped sentence plus a sentence-specific nuance, and the expected output is the full bolded span from the source sentence.

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---|---|---|
| Sentence (gapped) | `{{Sentence}}` | Rendered as HTML into a `<div id="prod-sentence">`. Inline JS replaces the visible text inside any `<b>` element with `＿＿＿`. |
| Hint label | — | Static text `Hint:` rendered above the nuance. |
| Meaning hint | `{{Meaning_Hint}}` | Displayed below the gapped sentence to disambiguate which use of the grammar is being tested. |

### JS Blanking Snippet

```javascript
(function () {
  var el = document.getElementById("prod-sentence");
  if (!el) return;
  var bolds = el.querySelectorAll("b");
  bolds.forEach(function (b) {
    b.textContent = "＿＿＿";
  });
})();
```

- Targets only `<b>` elements inside `#prod-sentence`.
- Uses `textContent` to replace the visible answer span only.
- The stored `Sentence` should bold the full tested chunk, not only the abstract grammar label. That keeps the Production Card focused on both grammar selection and formation.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---|---|---|
| Sentence (revealed) | `{{Sentence}}` | Re-rendered without the front-side blanking script, so the original bolded answer span is shown as the reveal. |
| Meaning hint | `{{Meaning_Hint}}` | Repeated for context continuity. |
| Grammar point | `{{GrammarPoint}}` | Canonical label for the concept being reviewed. |
| Formation | `{{Formation}}` | Mechanical formation rule shown for reinforcement. |
| Translation (collapsible) | `{{SentenceTranslation}}` | Native `<details>`/`<summary>` block. Collapsed by default. |
| Notes (collapsible) | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Only shown if the field is non-empty. |

---

## Conditional Logic

- `{{#Notes}}...{{/Notes}}` — The Notes collapsible is only rendered if `Notes` is non-empty.
- `{{SentenceTranslation}}` is always shown (not conditional).
- No audio field is used by this Note Type.

---

## Styling Notes (`style.css`)

- Matches the Comprehension Card Type closely for visual consistency.
- The gapped sentence stays central and prominent.
- `Meaning_Hint` is styled as a subdued prompt so it helps disambiguation without giving away the answer form.
- The revealed bolded answer span is colored `#1a6ebd` on the back.
