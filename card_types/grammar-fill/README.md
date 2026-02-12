# Grammar Fill-in-the-blank Card Type

## Goal

Master Japanese grammar production. The user sees a sentence with a missing grammar structure and must recall/produce the correct form based on context and a hint.

## Required Fields

- `Sentence` - The full Japanese sentence. Use `[]` to mark the position of the grammar point. (e.g., `明日、京都に[ ]。`)
- `Answer` - The correct grammar form to fill the gap. (e.g., `行きます`)
- `Meaning` - English translation of the sentence.
- `Hint` - A clue to guide production (e.g., dictionary form, particle, or specific nuance).
- `GrammarPoint` - The name of the grammar rule being tested.
- `Explanation` - (Optional) Additional notes on usage, conjugation, or common mistakes.

## How to use

1. **Front**: The card displays the sentence with a blank `_______`, the English translation, and a hint.
2. **Back**: Reveals the full sentence with the answer highlighted, along with the grammar point name and explanation.

## Card behavior

- Focuses on **active recall** of grammar structures rather than passive recognition.
- Uses `[]` syntax consistent with other card types in this repository.
- Provides a dedicated hint section to reduce ambiguity in production.
