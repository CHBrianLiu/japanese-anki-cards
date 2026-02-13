# Grammar Production Cloze Note Type

This note type is specialized for learning Japanese grammar through active production using Anki's cloze deletion feature.

## Fields

1. **Sentence**: The core Japanese sentence containing the grammar pattern.
   - Example: `雨が{{c1::降っている}}。`
   - **Inline Hint**: You can also use `{{c1::降っている::ongoing}}` to show `[ongoing]` on the front side.
2. **EnglishMeaning**: The English translation of the sentence.
   - Example: `It is raining.`
3. **GrammarPoint**: The name or form of the grammar being studied.
   - Example: `〜ている`
4. **Hint**: A context clue to help you choose the correct grammar pattern when multiple might fit.
   - Example: `ongoing action`
5. **Note**: Additional details, common mistakes, or extra examples for the grammar point.

## Generated Card Types

This note type generates one or more cloze cards based on the deletions in the **Sentence** field.

### 1. Grammar Production (Cloze)
- **Front**: Displays the **Sentence** with the grammar pattern blanked out, the **Hint**, and the **EnglishMeaning**.
- **Back**: Reveals the full **Sentence**, and shows the **GrammarPoint** for reference.

## Sample Entries

| Sentence (Cloze) | English Meaning | Grammar Point | Hint | Note |
| :--- | :--- | :--- | :--- | :--- |
| ここで靴を{{c1::脱がなければなりません::must}}。 | You must take off your shoes here. | 〜なければならない | obligation (formal) | `脱ぐ` [1]. Formal obligation. In casual speech, `なきゃいけない` is common. |
| 彼は先生の{{c1::ように::like}}日本語を話します。 | He speaks Japanese like a teacher. | 〜ように | similarity/likeness | `ように` [1]. Used for comparisons that are actually true or very similar. |
| 宿題を{{c1::している::in the middle of}}ところです。 | I am in the middle of doing my homework. | 〜ているところ | current state/action | `ところ` [0]. Focuses on the exact moment the action is occurring. |
| 甘いものを{{c1::食べすぎないように::trying not to}}しています。 | I am trying not to eat too many sweets. | 〜ないようにする | making an effort | `食べる` [2]. `〜ようにする` indicates a habitual effort or intention. |
| 雨が{{c1::降りだしました::started to}}。 | It started to rain (suddenly). | 〜だす | sudden start | `降る` [1]. `〜だす` implies an unexpected or sudden beginning. |
