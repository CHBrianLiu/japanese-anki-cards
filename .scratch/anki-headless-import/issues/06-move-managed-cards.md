# 06: Verify new managed Card placement in linked Decks

**What to build:** Newly generated repository-managed Cards use the approved existing normal Deck resolved from entry YAML's `deck` declaration. Existing Cards keep their current Deck placement, regardless of YAML. Verify the placement behavior after Note updates and make it reusable by Template-update integration without adding a command for existing-Card movement.

**Blocked by:** 04 — Add and update Notes directly from YAML.

**Status:** resolved

**Verification environment:** Use sandbox Collections/temporary fixtures and the dedicated environment documented in [`tools/headless_import/exploration.md`](../../../tools/headless_import/exploration.md). Setup may create existing fixture Decks; the updater must not. No personal Collection access or product backup/restore mechanism.

- [x] Resolve new managed Card targets from YAML `deck` through approved Collection-local links. Do not compare or report existing Card/YAML Deck differences.
- [x] Capture existing Card IDs before native Note/Template updates and limit any native placement operations to newly generated managed Cards. New Notes are added to their linked existing Deck through native APIs; newly generated Cards already there require no placement operation.
- [x] Reject filtered-Deck Cards and destinations, missing or ambiguous Deck links, and conflicting template Deck overrides; do not create Decks or change their options.
- [x] Preserve existing Card IDs, Deck IDs, review-history rows, and ordinary review due dates/intervals. Cover existing learning/relearning and review Cards without invoking moves on them.
- [x] Test existing Cards intentionally placed in another normal Deck, including multiple Card Types split across Decks: updates retain their placement and emit no mismatch warnings. Changing YAML `deck` affects future generated Cards only.
- [x] Report newly generated Card IDs, Card Types, and actual linked Deck placement. Leave unrelated Cards, including those generated for unrelated Notes by shared Template changes, outside managed placement; shared effects remain disclosed by ticket 05.
- [x] Demonstrate persisted placement after reopening, second-run idempotency, safe connection cleanup, and partial-failure/committed-progress reporting through public-command sandbox tests. Require fresh preview before retry; do not create backups or restore the target on failure.

## Comments

- 2026-11-16: Replaces the earlier existing-Card movement scope following user clarification. Ticket number, filename, and dependency on 04 are retained for stable references; guarded ticket 07 combines this behavior with ticket 05's Template-generated Cards. Earlier native-move feasibility findings remain historical evidence, not authorization to move existing Cards.
- 2026-11-16: User pivot: all placement work/tests use the documented sandbox environment, without a product backup/recovery mechanism. Existing scheduling/history and placement acceptance remain required and unchecked.
- 2026-11-16: Verified through public-command temporary sandbox tests using the dedicated environment. Extracted `place_new_managed_cards` for Note/Template-generated managed Cards; committed reports now include Card IDs, Card Type names, and actual Deck IDs/names, including placement failure. Covered split learning/relearning Cards with native moves forbidden, future-only YAML Deck changes, filtered generated Cards, retained review history, reopen/idempotency, and committed Template effects after placement failure with released connections and disposable resources. Retains the current README contract: exact-name Collection-local resolution with explicit application approval, not a separate links file; durable preview/approval guards belong to ticket 07. Fresh-preview retry leaves interrupted-run Cards in place because they are now existing Cards. No personal Collection, Deck creation/options changes, entry YAML/CSV edits, or product backups/restoration.
- 2026-11-16: Spec review identified omitted committed Card evidence for managed Notes not reached after a shared Template update and first placement failure. Added aggregate failure evidence for every managed delta and a two-managed-Note public-command regression test; unrelated generated Cards remain excluded. Standards review found no violations, only optional fixture cleanup.
