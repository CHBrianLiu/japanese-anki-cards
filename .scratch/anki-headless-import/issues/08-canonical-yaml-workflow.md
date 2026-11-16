# 08: Make YAML-to-Collection the canonical workflow

**What to build:** After the complete headless command is verified in the documented sandbox, authors edit YAML and apply it without a mandatory CSV-generation step. Repository guidance and validation describe this workflow consistently, while the existing CSV converter and artifacts remain an optional Desktop-import fallback. No personal-Collection verification or product backup mechanism is required for the transition.

**Blocked by:** 07 — Safely apply the complete workflow to an existing Collection.

**Status:** ready-for-agent

**Verification environment:** All workflow/regression tests and manual demonstrations use the dedicated environment and sandbox fixtures documented in [`tools/headless_import/exploration.md`](../../../tools/headless_import/exploration.md). Ticket 07's sandbox acceptance is the retirement gate; do not introduce a live smoke-test or backup gate.

- [ ] Update repository instructions, tooling guidance, Note Type workflow documentation, and relevant tests so the canonical edit/validate/preview/apply cycle uses YAML directly.
- [ ] Remove the requirement to regenerate CSV after each YAML edit; keep stable first-Field identity, schema/config alignment, required-value checks, native tags, and Field normalization requirements.
- [ ] Document YAML `deck` as the requested approved existing Deck for new managed Cards, separate Collection/Profile selection, unchanged existing Card placement without mismatch reporting, shared styling, repository-wins behavior, and personal-tag replacement.
- [ ] Document temporary WAL-consistent preview/rehearsal copies without forced source checkpoints, non-mutating media availability, disposable-only preview backend access, and Anki-closed operation. Explicitly state there is no product backup/restore mechanism, media recovery archive, or whole-run rollback guarantee. Document committed-progress reporting and fresh-preview/retry requirements instead of backup/recovery steps.
- [ ] Document REPO_DELETE through YAML/API tag updates followed by manual Note deletion, with YAML removal only after cleanup; retain the equivalent optional CSV fallback guidance.
- [ ] Keep the converter, existing generated CSV artifacts, and import symlinks as an explicitly optional fallback; do not delete or manually rewrite generated artifacts as part of retirement.
- [ ] Tests in the documented sandbox demonstrate that the canonical public-command workflow neither generates nor reads CSV, has no pre-apply backup/restore side effect, and that the optional CSV workflow still functions when explicitly invoked. Documentation examples and manual checks target sandbox Collections only.
- [ ] Clearly retain exclusions: no automatic Deck creation, existing-Card movement or Deck-mismatch reporting, schema migrations, media upload/deletion, Deck settings, Note/Card deletion, or sync.

## Comments

- 2026-11-16: The direct YAML path works in sandbox exploration, but mandatory CSV retirement remains blocked by guarded integration. Keep the existing optional fallback scope; this revision does not change repository-wide instructions or delete converter/artifacts.
- 2026-11-16: User pivot: sandbox-verified integrated acceptance is sufficient for canonical workflow transition; no live smoke test or backup mechanism is required. Document the exploration environment as the verification path and temporary preview copies as validation-only resources. Actual instruction/workflow retirement still waits for ticket 07; no repository-wide instructions or generated artifacts changed here.
