# 02: Prove headless Collection updates safely

**What to build:** A repeatable verification command demonstrates that the official Anki Python API can persist Note, Template, and Card-placement changes with Anki Desktop closed. It operates only on disposable Collections and produces evidence about identity, review history, scheduling, and idempotency before repository integration proceeds.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Resolve and report the installed Anki version and compatible Python package; use an existing repository virtual environment and stop with an actionable prerequisite message if compatibility or environment cannot be established.
- [ ] Use synthetic disposable Collections or explicitly provided consistent disposable copies; never open or mutate the live Collection during verification.
- [ ] Using native APIs, update a Note and retained Front/Back Templates and styling, then move an existing Card between normal Decks.
- [ ] Close and reopen the Collection and verify persisted content, retained Note IDs/GUIDs and Card IDs, unchanged review-history rows, and ordinary review due dates and intervals.
- [ ] Exercise conditional Card generation and learning/FSRS move behavior; report new Cards and native scheduling adjustments rather than claiming all scheduler properties remain identical.
- [ ] A second identical run introduces no duplicate objects or unnecessary changes; no-op Deck placement does not trigger avoidable updates.
- [ ] Lock failure stops safely, and connections are released after success and failure. Document that API operations save individually and a multi-operation run is not automatically atomic.
