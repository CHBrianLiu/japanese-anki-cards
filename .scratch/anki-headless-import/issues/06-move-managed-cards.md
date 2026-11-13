# 06: Move managed Cards to linked Decks

**What to build:** Changing an entry YAML target Deck moves that managed Note's existing Cards to its linked existing normal Deck using Anki's native operation, without recreating Cards or resetting review history.

**Blocked by:** 04 — Add and update Notes directly from YAML.

**Status:** ready-for-agent

- [ ] Preview and apply Card-placement differences for matched repository-managed Notes using approved Collection-local Deck links; entry YAML is authoritative.
- [ ] Move all applicable Cards of each selected Note after its Note updates, including newly generated conditional Cards, without directly rewriting scheduler data.
- [ ] Reject filtered-Deck Cards and destinations, missing or ambiguous Deck links, and conflicting template Deck overrides; do not create Decks or change their options.
- [ ] Preserve Card IDs and review-history rows; verify ordinary review due dates and intervals remain unchanged.
- [ ] Test and report native learning/relearning-step adjustments and FSRS memory-data effects separately from history preservation.
- [ ] Cards already in the target Deck are no-ops, and unrelated Notes/Cards remain untouched except any documented native destination-Deck scheduling effects.
- [ ] Demonstrate persisted placement after reopening, second-run idempotency, safe connection cleanup, and partial-failure reporting on disposable Collections.
