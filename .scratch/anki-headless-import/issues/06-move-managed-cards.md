# 06: Verify new managed Card placement in linked Decks

**What to build:** Newly generated repository-managed Cards use the approved existing normal Deck resolved from entry YAML's `deck` declaration. Existing Cards keep their current Deck placement, regardless of YAML. Verify the placement behavior after Note updates and make it reusable by Template-update integration without adding a command for existing-Card movement.

**Blocked by:** 04 — Add and update Notes directly from YAML.

**Status:** ready-for-agent

**Verification environment:** Use sandbox Collections/temporary fixtures and the dedicated environment documented in [`tools/headless_import/exploration.md`](../../../tools/headless_import/exploration.md). Setup may create existing fixture Decks; the updater must not. No personal Collection access or product backup/restore mechanism.

- [ ] Resolve new managed Card targets from YAML `deck` through approved Collection-local links. Do not compare or report existing Card/YAML Deck differences.
- [ ] Capture existing Card IDs before native Note/Template updates and limit any native placement operations to newly generated managed Cards. New Notes are added to their linked existing Deck through native APIs; newly generated Cards already there require no placement operation.
- [ ] Reject filtered-Deck Cards and destinations, missing or ambiguous Deck links, and conflicting template Deck overrides; do not create Decks or change their options.
- [ ] Preserve existing Card IDs, Deck IDs, review-history rows, and ordinary review due dates/intervals. Cover existing learning/relearning and review Cards without invoking moves on them.
- [ ] Test existing Cards intentionally placed in another normal Deck, including multiple Card Types split across Decks: updates retain their placement and emit no mismatch warnings. Changing YAML `deck` affects future generated Cards only.
- [ ] Report newly generated Card IDs, Card Types, and actual linked Deck placement. Leave unrelated Cards, including those generated for unrelated Notes by shared Template changes, outside managed placement; shared effects remain disclosed by ticket 05.
- [ ] Demonstrate persisted placement after reopening, second-run idempotency, safe connection cleanup, and partial-failure/committed-progress reporting through public-command sandbox tests. Require fresh preview before retry; do not create backups or restore the target on failure.

## Comments

- 2026-11-16: Replaces the earlier existing-Card movement scope following user clarification. Ticket number, filename, and dependency on 04 are retained for stable references; guarded ticket 07 combines this behavior with ticket 05's Template-generated Cards. Earlier native-move feasibility findings remain historical evidence, not authorization to move existing Cards.
- 2026-11-16: User pivot: all placement work/tests use the documented sandbox environment, without a product backup/recovery mechanism. Existing scheduling/history and placement acceptance remain required and unchecked.
