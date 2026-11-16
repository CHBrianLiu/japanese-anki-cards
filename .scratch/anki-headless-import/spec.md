# Headless Anki repository updates

**Status:** ready-for-agent

## Problem Statement

The repository holds Note Type schemas, Card Type Templates, styling, YAML Notes, and media references, but applying changes currently requires manual work in Anki Desktop. Authors generate CSV for Note imports, update Templates and styling separately, and reconcile Deck placement by hand. This creates friction and opportunities for drift between repository content and the Collection.

The author wants to update an existing Collection with Anki Desktop fully closed. Existing Notes and Cards must retain their identities and review history. All repository-defined Decks already have corresponding Decks in Anki, so updates should link to those Decks rather than create replacements. YAML should be the direct source for Note updates, without mandatory CSV generation.

## Solution

Provide a headless updater using Anki's official Python Collection interface. Authors edit repository content, preview validated changes against a consistent disposable Collection copy, and explicitly approve a guarded application to their selected existing Collection. The final product has no backup, restore, or recovery-package mechanism. All epic implementation verification, automated tests, rehearsals, and manual smoke/rendering checks use the isolated sandbox environment documented in [`tools/headless_import/exploration.md`](../../tools/headless_import/exploration.md), never a personal Collection.

The updater reconciles Notes by Note Type and exact stable first-Field ID, creates missing Note Types and Notes, updates retained Front/Back Templates and shared styling, and replaces managed Notes' tags. YAML's `deck` declaration determines the approved existing normal Deck for newly generated managed Cards. Existing Cards retain their current Deck placement, even when it differs from YAML; those differences are neither reported nor reconciled. The updater preserves existing identities and review history, reports automatic Card generation, and stops on unsafe or ambiguous conditions.

Align repository styling with Anki by maintaining one human-authored stylesheet per Note Type. After the headless workflow is verified, make YAML-to-Collection updates canonical and retain CSV tooling/artifacts as an optional Desktop-import fallback.

## User Stories

1. As a repository author, I want to apply changes with Anki Desktop closed, so that I do not need to navigate import dialogs or editing screens.
2. As a repository author, I want YAML to be the direct source for Notes, so that I do not need an intermediate CSV for ordinary updates.
3. As a repository author, I want the same source data to drive preview and application, so that the changes I approve match the changes performed.
4. As a repository author, I want an explicit target Collection, identified by its Desktop Profile when applicable, so that I cannot accidentally update another Collection. Each Desktop Profile owns one Collection; the Profile name is not a separate Collection name.
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
22. As a repository author, I want to resolve entry YAML `deck` declarations to approved existing Anki Decks, so that updates reuse my established Deck hierarchy without a second repository Deck definition.
23. As a repository author, I want entry YAML to determine placement for new Cards, so that changing its Deck declaration affects future Card creation rather than moving existing Cards.
24. As a repository author, I want missing, ambiguous, or invalid Deck links rejected, so that typos cannot create replacement Decks or misplace Cards.
25. As a learner, I want existing Cards left in their current Decks, so that repository updates preserve intentional manual placement and avoid Deck-move scheduling effects.
26. As a repository author, I want existing Card/YAML Deck differences ignored, so that preview does not produce unwanted placement warnings or proposed moves.
27. As a repository author, I want newly generated managed Cards placed in their linked YAML Deck, so that conditional or Template-driven Card creation has predictable placement.
28. As a repository author, I want one shared stylesheet per Note Type, so that repository styling matches Anki without a merging tool.
29. As a repository author, I want intentional Card Type visual differences preserved, so that shared styling does not flatten distinct learning presentations.
30. As a repository author, I want missing Note Types created from the approved schema and Templates, so that their YAML Notes can be imported without manual setup.
31. As a repository author, I want retained Front/Back Templates updated without rebuilding their identities, so that existing Cards remain associated with their Card Types.
32. As a repository author, I want unsupported structural changes rejected, so that Field or Card Type edits cannot silently delete Cards or migrate Note Types.
33. As a repository author, I want Note Type-wide effects disclosed and approved, so that I understand impacts on Notes outside the selected repository entries.
34. As a repository author, I want newly generated Cards reported and placed correctly, so that conditional content or Front Template changes do not create unnoticed misplaced Cards.
35. As a repository author, I want missing referenced media to block application, so that updated Notes do not silently contain broken media references.
36. As a repository author, I want no built-in backup or restore mechanism, so that the updater stays focused on validated repository updates.
37. As a repository author, I want the complete change verified in the documented sandbox, so that epic development and acceptance never touch my personal Collection.
38. As a repository author, I want stale approvals rejected, so that source or Collection changes cannot invalidate the preview unnoticed.
39. As a repository author, I want lock contention and concurrent runs to stop safely, so that multiple processes cannot compete to modify the Collection.
40. As a repository author, I want failures to report committed progress and require a fresh preview before retrying, so that I am not misled into assuming the entire run rolled back.
41. As a repository author, I want a second identical run to be a no-op, so that rerunning the updater does not create duplicates or unnecessary updates.
42. As a repository author, I want REPO_DELETE propagated as a tag without automatic deletion, so that I retain manual control over destructive cleanup.
43. As a repository author, I want missing YAML entries ignored rather than deleted from Anki, so that absence from a source selection is not treated as deletion permission.
44. As a repository author, I want repository instructions and tests to describe the YAML workflow consistently, so that future contributors do not need to follow obsolete mandatory CSV steps.
45. As a repository author, I want the existing CSV workflow retained as an optional fallback, so that Desktop text import remains available without blocking the canonical headless path.
46. As a maintainer, I want behavior verified through the public updater command in the documented sandbox environment, so that tests protect user outcomes without accessing a personal Collection.

## Implementation Decisions

### Module and public interface

- Build one deep updater module behind a small public command interface. Repository loading, validation, identity matching, Collection operations, disposable preview/rehearsal copies, and progress reporting remain implementation concerns rather than separately exposed interfaces callers must orchestrate. No backup or restore interface is provided.
- The public interface supports preview/rehearsal and explicitly approved application. Its required inputs identify repository content and the target Collection/profile. Entry YAML `deck` resolves by exact name in that Collection; no separate approved Deck links or mapping file is required. The exact command spelling is an implementation choice, not an established contract in this spec.
- Use the official Anki Python Collection interface and native mutation operations, not direct database writes, a GUI add-on, or independently generated package identities.
- Use a package compatible with the actual installed Desktop release. Resolve prerequisites before backend access; use an existing repository virtual environment and stop if a suitable environment is unavailable.
- Reports distinguish validation failures, proposed Field changes, committed operations, new Cards and their placement, tag replacement, and retry prerequisites. Existing Card/YAML Deck differences are not reported. Errors must identify the relevant Note/Note Type/Deck without exposing unrelated Collection content.

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
- Native Note or Front Template updates may generate missing Cards. Capture existing Card IDs before updates, report newly generated Cards, and place only newly generated managed Cards in the linked YAML Deck. Cards generated for unrelated Notes by shared Template updates are reported under Note Type-wide effects but their placement is not changed by the updater. Never remove retained empty Cards automatically.
- Repeated identical inputs should cause no unnecessary native mutations, duplicate objects, tag changes, or new-Card placement operations.

### Existing Deck resolution and placement

- Entry YAML's top-level `deck` declaration is authoritative for new managed Card placement, not Collection selection. Every entry source must contain a nonempty valid `deck`; configuration-only files need no Deck declaration. Note Type target-Deck documentation describes intended scope/default context without overriding the entry declaration.
- All repository Decks already have corresponding Anki Decks. Resolve YAML `deck` directly by exact hierarchical name to one existing normal Deck in the selected Collection. No approved-links JSON or alternate-name mapping is needed; do not create missing Decks.
- Resolve Deck IDs within the selected Collection rather than assuming IDs are portable to another Collection. Missing, ambiguous, or filtered targets fail before application.
- Add new Notes to their linked Deck through native APIs. After Note/Template updates, place only newly generated managed Cards that require placement; never move a Card whose ID existed before the update. Existing placement differences from YAML are ignored without warnings or proposed moves.
- Preserve existing review-history rows and ordinary review scheduling, including due dates and intervals. Verify existing Card Deck IDs remain unchanged; do not invoke Deck moves on existing learning/relearning or review Cards.
- Reject Cards currently in filtered Decks for the initial workflow. Do not alter Deck options or create Decks.

### Safety, media, and failure contract

- Never use the source Collection as an inspection-only dry run, even when the source is our sandbox. Backend opening can migrate a Collection; resolve compatibility beforehand and open the Anki backend for preview only on a consistent disposable copy.
- Require Anki Desktop closed and prevent simultaneous updater runs. Honor native locking failures and release backend connections on success and failure.
- Create temporary consistent preview/rehearsal database copies with SQLite's backup API, which includes committed WAL changes in the destination database. Do not force a checkpoint on the source or copy only `collection.anki2` while ignoring its WAL. Close the source SQLite connection before opening the disposable copy with Anki; do not open the source through Anki merely to prepare a preview. Release connections and clean up disposable resources on every exit path.
- Database copies are temporary preview/rehearsal inputs only, not retained backups or recovery packages. SQLite's backup API is a consistency primitive for those disposable copies, not a product backup feature. Make referenced media available for validation without source-media writes; do not create media recovery archives or provide restoration. Opening a disposable database may create its own WAL files.
- Rehearse the complete approved change, reopen the rehearsal Collection, and compare persisted identities, history, content, tags, Card counts, and scheduling. During this epic, both the selected target and rehearsal are sandbox Collections. Rehearsal never authorizes replacing the target Collection with the copy.
- Require explicit apply approval and revalidate source/target state before mutation. If it changed since rehearsal, stop and require a fresh rehearsal/approval. Sandbox verification does not authorize personal Collection access.
- Referenced media must already exist in the target Collection. Missing media fails validation; do not upload, rename, replace, or remove assets.
- Native operations save individually. Do not claim whole-run atomicity or promise rollback. Failures report committed progress, release locks, and require a fresh preview/approval before retrying; do not create backups, restore copies, or overwrite newer user work.
- REPO_DELETE remains metadata for manual deletion. Under the canonical API workflow, apply the tag through YAML, manually delete matching Notes, and remove YAML entries only after cleanup. Absence from YAML or a source selection never authorizes deletion.

### Workflow transition

- Preserve the eight ticket numbers and their blocking edges: shared-styling preparation and headless capability verification can start independently; YAML preview follows verification; Note application follows preview; Note Type/Template application follows styling preparation and Note application; new-Card placement verification follows Note application; guarded integration follows Template application and new-Card placement verification; canonical workflow retirement follows guarded integration. Ticket 06 replaces the previously planned existing-Card movement slice.
- Do not retire mandatory CSV generation before the complete API workflow is verified in the documented sandbox environment. No personal-Collection smoke test is a prerequisite. Then update instructions, guidance, and tests to make direct YAML preview/application canonical.
- Keep the converter, existing generated CSV artifacts, and import symlinks as an explicitly optional fallback. Remove the mandatory regeneration requirement without deleting these artifacts or hand-editing generated imports.

## Testing Decisions

- **Approved primary seam:** the public updater command interface, supplied with repository fixtures and real Anki Collections isolated in the documented sandbox environment. Both callers and integration tests exercise the same interface. No separate public interfaces are needed for each internal loading, matching, or backend operation.
- Good tests assert externally observable behavior: reports, rejection outcomes, persisted content after reopening, object identities, review-history preservation, placement, committed-progress/retry reporting, and idempotency. Do not assert internal call ordering or mock individual Anki methods as proof of integration correctness.
- Exercise the updater module end to end. Keep existing YAML/configuration and CSV regression tests as supporting coverage while their fallback remains supported, rather than replacing the primary seam with many new low-level tests.
- The verification environment is [`tools/headless_import/exploration.md`](../../tools/headless_import/exploration.md): the tool-specific `.venv`, compatible installed Anki package, tool-created sandbox Collections with matching manifests, and temporary isolated fixtures. Reuse its direct YAML imports, native tags, schema/Template creation, identity preservation, and repeat-run evidence. Its historical pre-import snapshots are not a requirement; remove that behavior from the canonical product path. Its Deck creation and existing-Card movement remain exploration-only behavior, not canonical updater scope.
- All eight tickets use this sandbox environment for new implementation work and acceptance verification. Build synthetic sandbox fixtures with existing Notes, review history, multiple Card Types, normal Decks, approved links, and media; use consistent disposable sandbox copies for preview/rehearsal. Setup may create fixture Decks/media separately from the updater. Do not open, copy, inspect, register, or mutate personal Collections or their media/profile registry for epic verification. Completed ticket evidence remains historical, not newly executed acceptance evidence.
- Test valid YAML addition/update and invalid YAML, missing requirements, unknown Fields, unquoted/empty IDs, duplicate source IDs, ambiguous Collection matches, incompatible schemas, and missing Deck/media references.
- Verify Note IDs/GUIDs, Card IDs, review-history rows, ordinary review due dates and intervals before and after updates. Include unrelated Notes, multiple Note Types with the same custom ID, and intentional tag replacement/clearing.
- Verify retained Template updates, newly created Note Types and Notes, shared styling/rendering, conditional/new Card generation, approved Note Type-wide effects, and structural-change rejection.
- Verify new managed Card placement, including conditional Cards and Cards generated by Template changes. Existing Cards intentionally in different normal Decks must retain their Deck IDs and ordinary scheduling without mismatch reports. Cover filtered-Deck rejection, conflicting template overrides, unrelated Cards, and second-run no-op placement.
- Verify deterministic per-Note add/update/unchanged summaries, Field before/after values, tag additions/removals, approved new-Card target resolution, and actual new-Card effects in rehearsal. Keep temporary paths and timestamps separate from deterministic summaries. Test WAL-inclusive snapshots and source database/media immutability during preview, including rejection paths.
- Test the guard contract through the command interface in the sandbox: incompatible versions, unavailable prerequisites, lock contention, wrong target, stale approval, disposable-copy/rehearsal failures, interruption after committed operations, and connection cleanup. Verify application has no pre-apply backup, media archive, or automatic restore side effect. Failure simulation may be internal to the test environment; it must not become an unnecessary public production interface.
- Run each valid scenario twice and verify the second run creates no duplicates or unnecessary mutations. Reopen Collections to prove persistence rather than trusting returned objects.
- Verify the canonical path neither generates nor reads CSV. Retain explicit fallback tests after mandatory CSV retirement.
- Styling tests cover intended Front/Back presentations and cross-Card-Type isolation; supplement automated assertions with a documented rendering check using sandbox Notes on intended clients where headless tests cannot represent client presentation faithfully. Close Desktop again before headless operations.
- Provide a documented sandbox-only end-to-end smoke-test procedure after isolated integration tests pass. Use the exploration environment and an explicitly selected tool-created sandbox with a matching manifest, compatible package, closed Desktop, approved links/ownership, and apply approval. Verify persisted results and a second-run no-op. No live/personal-Collection smoke-test procedure or execution is part of this epic.

## Out of Scope

- AnkiConnect or any requirement to run Anki Desktop during application.
- AnkiWeb synchronization, remote-device orchestration, or automatic full-sync decisions.
- Deck creation, Deck-option/preset changes, review-limit configuration, or deliberate rescheduling.
- Moving existing Cards to match YAML, reporting existing Card/YAML Deck mismatches, or reconciling manual Deck placement.
- Filtered-Deck handling beyond rejecting unsupported sources/destinations.
- Automatic Field/Card Type schema migrations, renames, reorderings, removals, or Note Type conversion.
- Automatic deletion of Notes, Cards, Templates, Decks, or media; deletion inferred from missing YAML entries; automatic cleanup of REPO_DELETE.
- Media upload, collision replacement, renaming, garbage collection, or asset generation.
- CSS merging/compilation tooling or per-individual-Note styling data.
- Personal-tag preservation/merging on managed Notes or Collection-wide tag removal.
- Direct Collection database mutation or rebuilding existing Notes/Cards to implement updates.
- Product backup creation/retention, media recovery archives, restore/rollback mechanisms, or automatic recovery. Temporary consistent preview/rehearsal copies remain in scope solely for non-mutating validation.
- Personal-Collection access for development, tests, acceptance, demonstrations, or smoke checks; sandbox verification does not establish compatibility with personal Collection data.
- CSV/converter/symlink deletion or removal of the optional Desktop-import fallback.
- UI development, building Anki from source, or replacing the live Collection with a rehearsal copy.

## Further Notes

- This spec synthesizes the approved investigation, user feedback, eight published tickets, and the user's explicit approval of the primary test seam. It does not authorize live Collection access or implementation merely by being published.
- Research established feasibility against Anki 26.09.4, with investigation dated 2026-11-10 and design feedback recorded 2026-11-13. Subsequent 2026-11-16 exploration prepared a dedicated virtual environment and imported all five repository Note Types into `sandbox-2gs8b2z0`, with 269 repository Notes and 488 Cards, persistence checks, and ten setup/import tests. Vocabulary Notes were verified by the user in Desktop. No personal Collection was accessed. The actual installed version/Profile and environment must still be checked at invocation.
- Tickets 01 and 02 are resolved; tickets 03–08 remain open. The exploration mutates its persistent sandbox after making historical pre-import snapshots and deliberately creates missing Decks; it does not satisfy the revised preview or existing-Deck approval contract. Its snapshot retention, Deck creation, and existing-Card movement must not enter the canonical updater. The exploration document remains an executed evidence record, not the current acceptance contract.
- Schema/tag terminology, stylesheet organization, and canonical workflow changes intentionally require coordinated repository-instruction updates during their implementation tickets. Existing instructions remain active until those changes land.
- Future requests for media handling, missing Deck creation, schema migrations, or sync require separately scoped work and approval; they must not silently enter this feature.

## Comments

- 2026-11-16: Revised after sandbox exploration and user clarification. Use SQLite backup snapshots without forcing source WAL checkpoints; Desktop Profiles each own one Collection rather than assigning the Collection a matching name. YAML `deck` is the requested existing Deck for new managed Cards. Retain explicit approved Collection-local links, ignore existing placement differences, and never move existing Cards. Ticket 06 now verifies new-Card placement; completed ticket history is preserved. This revision authorizes documentation changes only, not live Collection access.
- 2026-11-16: User pivot supersedes backup/recovery and live smoke-test requirements above: no backup mechanism in the final product, and all epic work/tests verify functionality in the sandbox environment documented in `tools/headless_import/exploration.md`. Temporary WAL-consistent preview/rehearsal copies remain solely to protect non-mutating preview, not for recovery. Existing Deck-link/placement rules, ticket numbers, dependencies, statuses, and historical evidence are preserved. This update changes planning documents only; it does not run imports/tests or authorize personal Collection access.
- 2026-11-16: User clarification for ticket 04 supersedes all separate approved-link requirements in this spec and remaining tickets: entry YAML `deck` alone identifies the existing normal Deck by exact hierarchical name within the explicitly selected Collection. No links file or Deck-specific approval workflow is needed. Explicit run/application approval remains required; missing/ambiguous/filtered Decks still fail, and existing Card placement remains unchanged.
