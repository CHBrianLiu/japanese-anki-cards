# 01: Move shared styling to each Note Type

**What to build:** Authors maintain one shared stylesheet per Note Type, matching Anki's native styling model. Each Card Type retains its separate Front/Back Templates and design rationale, and intentional visual differences remain intact. This is the repository preparation for headless Template updates, not a CSS compilation tool.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Migrate every repository Note Type to one human-authored shared stylesheet; no CSS merging or compilation tool is introduced.
- [x] Deliberately reconcile overlapping selectors and preserve intentional Card Type differences through shared rules or explicitly authored Card-Type-specific selectors.
- [x] Keep Card Type order stable where styling depends on template position.
- [x] Update repository instructions, Note Type documentation, and Card Type design documentation together so none still require per-Card-Type stylesheets.
- [x] Verify every Template Field reference against its parent schema and demonstrate Front/Back rendering without unintended style leakage between Card Types.
- [x] Existing YAML and CSV workflows continue to work; no Note content, stable IDs, review data, or live Collection is modified.

## Comments

- 2026-11-14: Implemented as `8947399`. Styling and YAML/CSV checks passed; intended-client rendering remains a manual check.
- 2026-11-14: Reviewed. One shared `style.css` per Note Type with no per-Card-Type stylesheets; overlapping selectors reconciled via explicit `.production` selectors; instructions/schema/design docs updated together; commit touched no YAML/CSV. `tools/test_shared_styling.py` passes (5 tests, including Template-field validation and headless-Chrome rendering/isolation). Marked resolved and merged into `main`.
