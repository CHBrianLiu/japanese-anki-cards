# Card Type: Production

**Parent Note Type:** `Spanish_Travel_Phrases`

---

## Learning Intention

Test whether the learner can actively recall a Spanish travel phrase from a simple English cue. This is a compact active-recall card designed for fast cramming, with pronunciation shown only on the back for self-checking.

---

## Front Template

**File:** `front.html`

| Element | Field | Notes |
|---------|-------|-------|
| Category | `{{Category}}` | Small topic label to orient the phrase. |
| English prompt | `{{English}}` | The cue the learner should translate into Spanish. |

The front is intentionally minimal: category, then the English prompt.

---

## Back Template

**File:** `back.html`

| Element | Field | Notes |
|---------|-------|-------|
| Category (repeated) | `{{Category}}` | Shown again for context continuity. |
| English prompt (repeated) | `{{English}}` | Repeated cue so the answer stays tied to the prompt. |
| Spanish answer | `{{Spanish}}` | The phrase to remember. |
| Pronunciation | `{{Pronunciation}}` | A learner-friendly pronunciation guide. |
| Notes | `{{Notes}}` | Conditional: `{{#Notes}}...{{/Notes}}`. Only shown if present. |

---

## Conditional Logic

- `{{#Notes}}...{{/Notes}}` renders only when `Notes` is non-empty.

---

## Styling Notes (`style.css`)

- Neutral, warm background for a simple travel-study feel.
- Large English cue on the front and large Spanish answer on the back.
- Pronunciation is visibly subordinate to the answer so it supports, rather than replaces, recall.
- Styling is scoped to this Card Type only.
