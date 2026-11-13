# 01: Move shared styling to each Note Type

**What to build:** Authors maintain one shared stylesheet per Note Type, matching Anki's native styling model. Each Card Type retains its separate Front/Back Templates and design rationale, and intentional visual differences remain intact. This is the repository preparation for headless Template updates, not a CSS compilation tool.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Migrate every repository Note Type to one human-authored shared stylesheet; no CSS merging or compilation tool is introduced.
- [ ] Deliberately reconcile overlapping selectors and preserve intentional Card Type differences through shared rules or explicitly authored Card-Type-specific selectors.
- [ ] Keep Card Type order stable where styling depends on template position.
- [ ] Update repository instructions, Note Type documentation, and Card Type design documentation together so none still require per-Card-Type stylesheets.
- [ ] Verify every Template Field reference against its parent schema and demonstrate Front/Back rendering without unintended style leakage between Card Types.
- [ ] Existing YAML and CSV workflows continue to work; no Note content, stable IDs, review data, or live Collection is modified.
