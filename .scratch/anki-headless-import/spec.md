# Headless Anki repository updates

**Status:** ready-for-agent

## Problem Statement

The repository holds Note Type schemas, Card Type Templates, styling, YAML Notes, and media references, but applying changes currently requires manual work in Anki Desktop. Authors generate CSV for Note imports, update Templates and styling separately, and reconcile Deck placement by hand. This creates friction and opportunities for drift between repository content and the Collection.

The author wants to update an existing Collection with Anki Desktop fully closed. Existing Notes and Cards must retain their identities and review history. All repository-defined Decks already have corresponding Decks in Anki, so updates should link to those Decks rather than create replacements. YAML should be the direct source for Note updates, without mandatory CSV generation.

## Solution

Provide a headless updater using Anki's official Python Collection interface. Authors edit repository content, preview validated changes against a consistent disposable Collection copy, and explicitly approve a guarded application to their selected existing Collection.

The updater reconciles Notes by Note Type and exact stable first-Field ID, creates missing Note Types and Notes, updates retained Front/Back Templates and shared styling, replaces managed Notes' tags, and moves their Cards to approved existing normal Decks. It preserves existing identities and review history, reports automatic Card generation and native scheduling effects, and stops on unsafe or ambiguous conditions.

Align repository styling with Anki by maintaining one human-authored stylesheet per Note Type. After the headless workflow is verified, make YAML-to-Collection updates canonical and retain CSV tooling/artifacts as an optional Desktop-import fallback.

## User Stories

1. As a repository author, I want to apply changes with Anki Desktop closed, so that I do not need to navigate import dialogs or editing screens.
2. As a repository author, I want YAML to be the direct source for Notes, so that I do not need an intermediate CSV for ordinary updates.
3. As a repository author, I want the same source data to drive preview and application, so that the changes I approve match the changes performed.
4. As a repository author, I want an explicit target Collection and profile, so that I cannot accidentally update another Collection.
5. As a repository author, I want the updater to verify package compatibility with my installed Anki version, so that routine updates do not silently upgrade or downgrade my Collection.
6. As a repository author, I want missing environment prerequisites reported clearly, so that setup problems do not lead to unsafe installations or Collection access.
7. As a repository author, I want invalid YAML and schema/config disagreements rejected before application, so that malformed content cannot produce partial imports.
8. As a repository author, I want required Fields and unknown Fields validated, so that every imported Note matches its approved Note Type.
9. As a repository author, I want quoted, nonempty stable IDs enforced, so that YAML parsing cannot corrupt Note identity.
10. As a repository author, I want duplicate IDs detected across entry files, so that one repository identity cannot refer to multiple Notes.
11. As a repository author, I want ambiguous existing Note matches rejected, so that the updater never guesses which Note to overwrite.
12. As a learner, I want existing Notes updated in place, so that their internal IDs and GUIDs remain stable.
13. As a learner, I want existing Cards retained during content updates, so that review history and learning progress are not reset.
14. As a repository author, I want missing Notes added through Anki's native operations, so that Anki generates their internal identities and Cards correctly.
15. As a repository author, I want repository-managed Field content to win over Anki edits, so that repeated updates converge on the repository source.
16. As a repository author, I want existing HTML normalization preserved, so that switching from CSV does not unexpectedly change displayed content.
17. As a repository author, I want native tags treated separately from ordinary Fields, so that the repository schema matches Anki's actual Note representation.
18. As a repository author, I want YAML tags to replace all tags on managed Notes, so that I do not need personal-tag merging rules.
19. As a repository author, I want empty or omitted YAML tags to clear managed Notes' tags, so that tag removal is predictable.
20. As a repository author, I want tag removals included in preview, so that replacement of personal tags is visible before application.
21. As a learner, I want unrelated Notes left alone, so that repository updates do not overwrite personal content elsewhere in my Collection.
22. As a repository author, I want to link repository Deck definitions to existing Anki Decks, so that updates reuse my established Deck hierarchy.
23. As a repository author, I want entry YAML to determine target Deck placement, so that changing its Deck declaration has a clear effect.
24. As a repository author, I want missing, ambiguous, or invalid Deck links rejected, so that typos cannot create replacement Decks or misplace Cards.
25. As a learner, I want Cards moved without recreation, so that changing a Deck does not destroy review history.
26. As a learner, I want native learning-step and FSRS effects explained, so that I understand adjustments caused by a Deck move.
27. As a repository author, I want Cards already in the correct Deck skipped, so that repeated runs avoid unnecessary changes.
28. As a repository author, I want one shared stylesheet per Note Type, so that repository styling matches Anki without a merging tool.
29. As a repository author, I want intentional Card Type visual differences preserved, so that shared styling does not flatten distinct learning presentations.
30. As a repository author, I want missing Note Types created from the approved schema and Templates, so that their YAML Notes can be imported without manual setup.
31. As a repository author, I want retained Front/Back Templates updated without rebuilding their identities, so that existing Cards remain associated with their Card Types.
32. As a repository author, I want unsupported structural changes rejected, so that Field or Card Type edits cannot silently delete Cards or migrate Note Types.
33. As a repository author, I want Note Type-wide effects disclosed and approved, so that I understand impacts on Notes outside the selected repository entries.
34. As a repository author, I want newly generated Cards reported and placed correctly, so that conditional content or Front Template changes do not create unnoticed misplaced Cards.
35. As a repository author, I want missing referenced media to block application, so that updated Notes do not silently contain broken media references.
36. As a repository author, I want a consistent recoverable backup before live access, so that failures or unexpected changes have a recovery path.
37. As a repository author, I want a disposable rehearsal of the complete change, so that I can verify behavior before touching my real Collection.
38. As a repository author, I want stale approvals rejected, so that source or Collection changes cannot invalidate the preview unnoticed.
39. As a repository author, I want lock contention and concurrent runs to stop safely, so that multiple processes cannot compete to modify the Collection.
40. As a repository author, I want failures to report committed progress and recovery guidance, so that I am not misled into assuming the entire run rolled back.
41. As a repository author, I want a second identical run to be a no-op, so that rerunning the updater does not create duplicates or unnecessary updates.
42. As a repository author, I want REPO_DELETE propagated as a tag without automatic deletion, so that I retain manual control over destructive cleanup.
43. As a repository author, I want missing YAML entries ignored rather than deleted from Anki, so that absence from a source selection is not treated as deletion permission.
44. As a repository author, I want repository instructions and tests to describe the YAML workflow consistently, so that future contributors do not need to follow obsolete mandatory CSV steps.
45. As a repository author, I want the existing CSV workflow retained as an optional fallback, so that Desktop text import remains available without blocking the canonical headless path.
46. As a maintainer, I want behavior verified through the public updater command with disposable Collections, so that tests protect user outcomes rather than internal implementation choices.

## Implementation Decisions

### Module and public interface

- Build one deep updater module behind a small public command interface. Repository loading, validation, identity matching, Collection operations, backup/rehearsal, and progress reporting remain implementation concerns rather than separately exposed interfaces callers must orchestrate.
- The public interface supports preview/rehearsal and explicitly approved application. Its required inputs identify repository content, the target Collection/profile, and approved Deck links. The exact command spelling and configuration encoding are implementation choices, not established contracts in this spec.
- Use the official Anki Python Collection interface and native mutation operations, not direct database writes, a GUI add-on, or independently generated package identities.
- Use a package compatible with the actual installed Desktop release. Resolve prerequisites before backend access; use an existing repository virtual environment and stop if a suitable environment is unavailable.
- Reports distinguish validation failures, proposed changes, committed operations, new Cards, tag replacement, placement changes, scheduling effects, and recovery prerequisites. Errors must identify the relevant Note/Note Type/Deck without exposing unrelated Collection content.

### Repository source contract and preparation

- Preserve authoritative Note Type schemas and ordered ordinary Fields, with stable first-Field custom IDs. Keep Card Type Front/Back Templates and design rationale separate.
- Move styling to one human-authored shared stylesheet per Note Type. Reconcile overlapping declarations deliberately and author any Card-Type-specific differences directly. Do not introduce CSS compilation or merging tooling.
- Validate Template references against ordinary Fields and Anki's native special fields, including `{{Tags}}`.
- Correct schema/config terminology so tags are native entry metadata, not an extra ordinary Note Type Field. Preserve optional legacy CSV column mapping during the transition.
- Parse and validate YAML directly: Note Type, entry target Deck, nonempty entry lists, required values, unknown Fields, quoted nonempty identity strings, and duplicate custom IDs within each Note Type across all source entry files.
- Preserve the current intended HTML Field normalization: absent optional values become empty strings, other content is trimmed, and internal line breaks become HTML line breaks consistently with the existing converter. Parse native tags separately from HTML Fields.
- Update instructions, schemas/configuration, and design documentation together when their contracts change. Before canonical workflow retirement, existing YAML edits still follow the active CSV regeneration rule; the spec itself does not amend it.

### Reconciliation and ownership

- Match a repository Note by Note Type and exact first-Field custom ID. Preserve Anki's existing Note ID/GUID and Card identities; let Anki generate internal identities for new Notes.
- Reject ambiguous matches and duplicate IDs rather than picking a Note or creating another duplicate. Reject unsupported existing schema mismatches rather than attempting automatic conversion.
- Repository-managed ordinary Field content and native tags are authoritative. YAML tags replace the complete tag set on matched managed Notes; absent, null, or empty tags clear it. Personal tags are not merged.
- Unmatched Notes remain untouched. Shared Templates/styling inherently affect every Note of a Note Type, so those effects and ownership must be explicitly approved rather than described as entry-local updates.
- Create missing Note Types from the approved ordered schema, Templates, and shared styling, then import their Notes. For existing Note Types, only update retained Templates and styling; retain Field/template identities, ordinals, and unrelated metadata.
- Reject existing Field/Card Type additions, removals, renames, reorderings, and Note Type conversions. Preserve template Deck overrides, but reject conflicts with requested placement rather than silently editing overrides.
- Native Note or Front Template updates may generate missing Cards. Report those effects and place newly generated managed Cards after content/Template updates. Never remove retained empty Cards automatically.
- Repeated identical inputs should cause no unnecessary native mutations, duplicate objects, tag changes, or Deck moves.

### Existing Deck links and placement

- Entry YAML is authoritative for target Deck placement. Note Type target-Deck documentation describes intended scope/default context without overriding the entry declaration.
- All repository Decks already have corresponding Anki Decks. Resolve explicit approved links to existing normal Decks in the selected Collection; exact hierarchical names may propose matches, but do not silently create missing Decks.
- Validate resolved Deck IDs against the selected Collection rather than assuming IDs are portable to another Collection. Missing, ambiguous, filtered, or conflicting links fail before application.
- Move applicable Cards of managed Notes through the native Deck operation after Note/Template updates. Cards already in their target Deck are skipped.
- Preserve review history and ordinary review due dates/intervals. Do not promise every scheduling property remains byte-for-byte identical: native learning/relearning-step and FSRS memory-data effects must be reported and tested, including documented effects on the destination Deck.
- Reject Cards currently in filtered Decks for the initial workflow. Do not alter Deck options or create Decks.

### Safety, media, and failure contract

- Never use the live Collection as an inspection-only dry run. Backend opening can migrate a Collection; resolve compatibility beforehand and rehearse only on a consistent disposable copy.
- Require Anki Desktop closed and prevent simultaneous updater runs. Honor native locking failures and release backend connections on success and failure.
- Obtain a verified consistent backup before opening the live Collection. Account for WAL state and preserve media for recovery, even though this feature does not modify media.
- Rehearse the complete approved change, reopen the rehearsal Collection, and compare persisted identities, history, content, tags, Card counts, and scheduling. Rehearsal does not authorize replacing the live Collection with the copy.
- Require explicit live-apply approval and revalidate source/target state before mutation. If it changed since rehearsal, stop and require a fresh rehearsal/approval.
- Referenced media must already exist in the target Collection. Missing media fails validation; do not upload, rename, replace, or remove assets.
- Native operations save individually. Do not claim whole-run atomicity or assume media/database rollback covers an entire sequence. Failures report committed progress, release locks, and provide recovery guidance without automatically overwriting newer user work.
- REPO_DELETE remains metadata for manual deletion. Under the canonical API workflow, apply the tag through YAML, manually delete matching Notes, and remove YAML entries only after cleanup. Absence from YAML or a source selection never authorizes deletion.

### Workflow transition

- Preserve the eight approved tickets and their blocking edges: shared-styling preparation and headless capability verification can start independently; YAML preview follows verification; Note application follows preview; Note Type/Template application follows styling preparation and Note application; Card movement follows Note application; guarded integration follows Template application and Card movement; canonical workflow retirement follows guarded integration.
- Do not retire mandatory CSV generation before the complete API workflow is verified. Then update instructions, guidance, and tests to make direct YAML preview/application canonical.
- Keep the converter, existing generated CSV artifacts, and import symlinks as an explicitly optional fallback. Remove the mandatory regeneration requirement without deleting these artifacts or hand-editing generated imports.

## Testing Decisions

- **Approved primary seam:** the public updater command interface, supplied with repository fixtures and disposable real Anki Collections. Both callers and integration tests exercise the same interface. No separate public interfaces are needed for each internal loading, matching, or backend operation.
- Good tests assert externally observable behavior: reports, rejection outcomes, persisted content after reopening, object identities, review-history preservation, placement, recovery guidance, and idempotency. Do not assert internal call ordering or mock individual Anki methods as proof of integration correctness.
- Exercise the updater module end to end. Keep existing YAML/configuration and CSV regression tests as supporting coverage while their fallback remains supported, rather than replacing the primary seam with many new low-level tests.
- Prior art is the repository's Python unittest-based converter suite: synthetic temporary YAML/configuration fixtures, invalid-input rejection, required/optional Field behavior, stable-ID validation, tags-column mapping, and normalization. Reuse these fixture concepts, but there is currently no Collection integration suite or demonstrated live update.
- Build synthetic disposable Collections with existing Notes, review history, multiple Card Types, normal Decks, and approved links. Include consistent disposable copies when testing preservation against representative existing data. Automated tests never access a real user Collection.
- Test valid YAML addition/update and invalid YAML, missing requirements, unknown Fields, unquoted/empty IDs, duplicate source IDs, ambiguous Collection matches, incompatible schemas, and missing Deck/media references.
- Verify Note IDs/GUIDs, Card IDs, review-history rows, ordinary review due dates and intervals before and after updates. Include unrelated Notes, multiple Note Types with the same custom ID, and intentional tag replacement/clearing.
- Verify retained Template updates, newly created Note Types and Notes, shared styling/rendering, conditional/new Card generation, approved Note Type-wide effects, and structural-change rejection.
- Verify existing normal Deck movement and persisted placement, including new Cards generated by Template changes. Cover no-op moves, filtered-Deck rejection, conflicting template overrides, and learning/FSRS adjustments without demanding unsupported byte-for-byte scheduler equality.
- Test the guard contract through the command interface: incompatible versions, unavailable prerequisites, lock contention, wrong target, stale approval, backup/rehearsal failures, interruption after committed operations, and connection cleanup. Failure simulation may be internal to the test environment; it must not become an unnecessary public production interface.
- Run each valid scenario twice and verify the second run creates no duplicates or unnecessary mutations. Reopen Collections to prove persistence rather than trusting returned objects.
- Verify the canonical path neither generates nor reads CSV. Retain explicit fallback tests after mandatory CSV retirement.
- Styling tests cover intended Front/Back presentations and cross-Card-Type isolation; supplement automated assertions with a documented rendering check on intended clients where headless tests cannot represent client presentation faithfully.
- Provide an opt-in live smoke-test procedure after disposable integration tests pass. It requires explicit approval, a verified backup, compatible environment, closed Desktop, and recovery guidance; it is never the default automated test target.

## Out of Scope

- AnkiConnect or any requirement to run Anki Desktop during application.
- AnkiWeb synchronization, remote-device orchestration, or automatic full-sync decisions.
- Deck creation, Deck-option/preset changes, review-limit configuration, or deliberate rescheduling.
- Filtered-Deck handling beyond rejecting unsupported sources/destinations.
- Automatic Field/Card Type schema migrations, renames, reorderings, removals, or Note Type conversion.
- Automatic deletion of Notes, Cards, Templates, Decks, or media; deletion inferred from missing YAML entries; automatic cleanup of REPO_DELETE.
- Media upload, collision replacement, renaming, garbage collection, or asset generation.
- CSS merging/compilation tooling or per-individual-Note styling data.
- Personal-tag preservation/merging on managed Notes or Collection-wide tag removal.
- Direct Collection database mutation or rebuilding existing Notes/Cards to implement updates.
- CSV/converter/symlink deletion or removal of the optional Desktop-import fallback.
- UI development, building Anki from source, or replacing the live Collection with a rehearsal copy.

## Further Notes

- This spec synthesizes the approved investigation, user feedback, eight published tickets, and the user's explicit approval of the primary test seam. It does not authorize live Collection access or implementation merely by being published.
- Research established feasibility against Anki 26.09.4, with investigation dated 2026-11-10 and design feedback recorded 2026-11-13. No updater, package installation, or Collection integration tests have been completed as part of that investigation. The actual installed version/profile and environment must be established during implementation, not assumed from the research baseline.
- The initial frontier is shared Note Type styling and headless capability verification. Preserve existing ticket numbers and dependencies; this spec supplements them rather than closing, modifying, or replacing them.
- Schema/tag terminology, stylesheet organization, and canonical workflow changes intentionally require coordinated repository-instruction updates during their implementation tickets. Existing instructions remain active until those changes land.
- Future requests for media handling, missing Deck creation, schema migrations, or sync require separately scoped work and approval; they must not silently enter this feature.
