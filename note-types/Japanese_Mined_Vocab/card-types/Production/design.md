# Card Type: Production

**Parent Note Type:** `Japanese_Mined_Vocab`

---

## Learning Intention

Test whether the learner can actively recall the correct Japanese vocabulary word given only the sentence context (with the target word blanked out) and a native-language meaning hint. This is an active recall card: the stimulus is a gapped sentence plus a meaning, and the expected output is retrieval of the Japanese word (and awareness of its required conjugation).

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---------|-------|-------|
| Sentence (gapped) | `{{Sentence}}` | Rendered as HTML into a `<div id="prod-sentence">`. A small inline JS snippet immediately replaces the `textContent` of any `<b>` elements with `＿＿＿`, hiding the target word. |
| Hint label | — | Static text "Hint:" rendered above the meaning. |
| Meaning hint | `{{Meaning}}` | Displayed below the gapped sentence as a disambiguation hint. |

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

- Targets only `<b>` elements inside `#prod-sentence` to avoid unintended side effects.
- Uses `textContent` (not `innerHTML`) to prevent XSS concerns and to replace the visible text only.
- Wrapped in an IIFE to avoid polluting the global scope.
- Uses fullwidth underscores (`＿＿＿`) for a visually clear blank that matches Japanese text width.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---------|-------|-------|
| Sentence (gapped, repeated) | `{{Sentence}}` | Shown again at top with `＿＿＿` still in place, for context continuity. No JS is run on the back — the `<b>` tag is intact and colored blue, but the gapped state is preserved by not running the script again. **Note:** The front content is not automatically carried over in Anki; the back template re-renders the sentence. On the back the `<b>` tag renders normally (showing the conjugated word in blue), which serves as the answer reveal for the gapped sentence. |
| Meaning hint | `{{Meaning}}` | Repeated to maintain context. |
| Dictionary form | `{{TargetWord}}` | Prominent display of the base form of the word. |
| Reading | `{{Reading}}` | Kana reading shown in parentheses. |
| Translation (collapsible) | `{{SentenceTranslation}}` | Native `<details>`/`<summary>` block. Collapsed by default. |
| Notes (collapsible) | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Only shown if the field is non-empty. |

> **Note on back sentence reveal:** Anki re-renders the back template independently. On the back, the JS blanking script is not included, so `<b>` text is shown in full (colored blue), effectively revealing the answer within the sentence. This is intentional — the learner first sees the gapped front, then flips to see the full sentence with the answer highlighted.

---

## Conditional Logic

- `{{#Notes}}...{{/Notes}}` — The Notes collapsible is only rendered if `Notes` is non-empty.
- `{{SentenceTranslation}}` is always shown (not conditional).
- No `{{#Audio}}` block on this card type — audio is only on the Comprehension back.

---

## Styling Notes (`style.css`)

- Identical font stack and base layout to the Comprehension card for visual consistency.
- `.hint-label` and `.hint` classes style the meaning hint with subdued color and italic text.
- The `<b>` tag inside `.sentence` is styled blue (`#1a6ebd`) — on the front this is invisible (replaced by JS), on the back it highlights the revealed answer.
- Styling is scoped to this Card Type; no global stylesheet is assumed.
