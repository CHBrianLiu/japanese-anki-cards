# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the repository.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root: the single-context domain vocabulary.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If these files don't exist, **proceed silently**. Don't flag their absence or suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

This repository uses a single-context layout. Paths are relative to the repository root:

```text
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       └── NNNN-decision-slug.md
├── media/
└── note-types/
```

This setup records the layout; it does not create an empty glossary or ADRs.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

Keep domain vocabulary consistent with the official Anki terminology required by `AGENTS.md`. Note Type schemas remain authoritative in their `note-type.md` files; Card Type rationale remains in their `design.md` files.

If the concept you need isn't in the glossary yet, either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> Contradicts ADR-NNNN (decision title), but worth reopening because…
