# 02: Prove headless Collection updates safely

**What to build:** A repeatable verification command demonstrates that the official Anki Python API can persist Note, Template, and Card-placement changes with Anki Desktop closed. It operates only on disposable Collections and produces evidence about identity, review history, scheduling, and idempotency before repository integration proceeds.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Resolve and report the installed Anki version and compatible Python package; use an existing repository virtual environment and stop with an actionable prerequisite message if compatibility or environment cannot be established.
- [x] Use synthetic disposable Collections or explicitly provided consistent disposable copies; never open or mutate the live Collection during verification.
- [x] Using native APIs, update a Note and retained Front/Back Templates and styling, then move an existing Card between normal Decks.
- [x] Close and reopen the Collection and verify persisted content, retained Note IDs/GUIDs and Card IDs, unchanged review-history rows, and ordinary review due dates and intervals.
- [x] Exercise conditional Card generation and learning/FSRS move behavior; report new Cards and native scheduling adjustments rather than claiming all scheduler properties remain identical.
- [x] A second identical run introduces no duplicate objects or unnecessary changes; no-op Deck placement does not trigger avoidable updates.
- [x] Lock failure stops safely, and connections are released after success and failure. Document that API operations save individually and a multi-operation run is not automatically atomic.

## Comments

- 2026-11-14: Implemented as `0bfa9c6` and reviewed against all seven criteria. Matching-package disposable Collection tests passed. Findings and reproduction steps are in [`verification-findings.md`](../verification-findings.md). The verification command does not itself enforce that Anki Desktop is closed; the guarded workflow must do so. This ticket's resolution is not approval to update a live Collection.
