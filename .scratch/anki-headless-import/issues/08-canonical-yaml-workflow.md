# 08: Make YAML-to-Collection the canonical workflow

**What to build:** Authors edit YAML and apply it through the verified headless command without a mandatory CSV-generation step. Repository guidance and validation describe this workflow consistently, while the existing CSV converter and artifacts remain an optional Desktop-import fallback.

**Blocked by:** 07 — Safely apply the complete workflow to an existing Collection.

**Status:** ready-for-agent

- [ ] Update repository instructions, tooling guidance, Note Type workflow documentation, and relevant tests so the canonical edit/validate/preview/apply cycle uses YAML directly.
- [ ] Remove the requirement to regenerate CSV after each YAML edit; keep stable first-Field identity, schema/config alignment, required-value checks, native tags, and Field normalization requirements.
- [ ] Document existing-Deck linking, shared styling, repository-wins behavior, personal-tag replacement, backup/rehearsal requirements, and Anki-closed operation.
- [ ] Document REPO_DELETE through YAML/API tag updates followed by manual Note deletion, with YAML removal only after cleanup; retain the equivalent optional CSV fallback guidance.
- [ ] Keep the converter, existing generated CSV artifacts, and import symlinks as an explicitly optional fallback; do not delete or manually rewrite generated artifacts as part of retirement.
- [ ] Tests demonstrate that the canonical workflow neither generates nor reads CSV and that the optional CSV workflow still functions when explicitly invoked.
- [ ] Clearly retain exclusions: no automatic Deck creation, schema migrations, media upload/deletion, Deck settings, Note/Card deletion, or sync.
