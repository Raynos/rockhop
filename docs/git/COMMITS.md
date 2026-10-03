# Commit conventions

AGENTS.md points here; this is the canonical policy for every tool.
Keep one coherent finding in each round's commit.
Commit early and often directly on `main`: land a finished finding before
starting the next experiment. Do not accumulate an entire plan or session.
Stable experimental recipes and evidence may land as explicitly unaccepted
checkpoints while visual/device review continues; keep their exports out of
normal player paths until the required review passes.

## Message

Use type(scope): finding, at most 72 characters, with no trailing period.
Use an imperative verb for a change; a measured finding can state the result.
Types: feat, fix, docs, design, art, style, refactor, perf, test, build, ci,
chore, revert. Scope is optional, lowercase, and names an area or course
(boot, physics, map, c1, hooks). An optional ! marks a breaking change.
Design covers experiments and decisions; art covers visual assets.

After a blank line, explain why and the resulting behavior. Keep inventories,
ask/plan IDs and session bookkeeping out of the subject. Wrap ordinary prose
at 72 characters; paths and URLs can run longer. Include Validation: with
actual checks and outcomes, or explain why none ran. Cite Evidence: and Ask:
when applicable. State material limits; a proxy never implies a phone pass.

AI commits end with a separate trailer block:

    Assisted-by: tool:actual-model

Desktop attribution comes from the active session's runtime metadata, never a
default config or another session. For Codex, run
`node .githooks/resolve-attribution.mjs`: the default route reads only the
matching local session and prints its latest recorded model. Unknown and other
placeholders are forbidden. Do not copy session records into the repository.
If resolution fails, investigate the active runtime; do not invent attribution.

Cloud/delegated sessions may lack a local session record. When the user explicitly
supplies the tool/model label, set `CODEX_CLOUD_ATTRIBUTION_FILE` to a reviewed JSON
file under `docs/evidence/`, then run the same resolver from the repository. This
is an explicit user declaration, not automatic model detection or a fallback for
failed desktop metadata. A missing, malformed or stale declaration fails closed.
The checker preserves the supplied tool spelling (`Codex` or `codex`) in this
route; the desktop route continues to require canonical `Codex`.

The declaration contains exactly `schemaVersion: 1`, `execution: "cloud"`,
`source: "user-provided"`, the active `session`, `tool`, `model`, and an
`authorization` string recording the user's exact label. It must be inside the
repository and at most 16 KiB. The resolver prints the Assisted-by trailer plus
mandatory Attribution-source, Attribution-session and Attribution-evidence
trailers. Keep all four together in the final trailer block. The evidence trailer
pins the declaration's path and SHA256; those exact bytes must also be staged
in the commit index. Changed or unstaged declarations invalidate the trailers.
Keep Assisted-by last, after the provenance trailers. No cloud route reads local
session metadata or silently substitutes a model. Human-bypass flags do not bypass an explicit cloud declaration.

Example authorized declaration and exact user quotes:
`docs/evidence/cloud-commit-attribution-2026-10-03/user-declaration.json`.
Use the user's statement only for its authorized scope; a prior declaration does
not establish another session's model. Validation proves syntax/session/provenance
consistency; truthful user authorization remains the committing parent's duty.

Cloud declarations accept different explicit model labels for different sessions;
the example's Astra-6 label is never a default. A new authorized model requires
updated declaration bytes and newly resolved trailers. Tests cover Sol and Luna
sessions, cross-session rejection, model changes, and an absent cloud route.

The inspected Codex CLI 0.159.3 app-server `Thread.model` field is configured or
latest persisted model, explicitly not per-turn execution telemetry. Its `Turn`
type has no executed-model field. A model picker, `model/list`, config, thread
setting or assistant self-report cannot establish the actual execution model.
Use an authoritative matching runtime record if exposed; otherwise preserve the
explicit user-provided provenance above. See
`docs/evidence/cloud-model-metadata-2026-10-03/` for the bounded protocol audit.

Human coauthors can use Co-authored-by; AI assistance uses Assisted-by.
A genuinely human commit can set SKIP_ATTRIB=1 to skip only the
attribution requirement.

Example format (validation is illustrative, not a test claim):

    fix(boot): recover a lost Safari rendering context

    Safari can lose the context during startup and leave the player stuck.
    Retry renderer creation so a transient loss can recover.

    Validation: startup regression checks pass; physical iPhone pending.
    Evidence: docs/evidence/ios-webgl-context-retry/

    Assisted-by: Codex:gpt-6.1-sol

## Journal

Commits with at least 30 added/deleted non-journal text lines require an
entry under project/journal/ in the same commit. Under 30, it is optional.
Count additions plus deletions across text files; exclude the journal
itself. Binary blobs contribute no text lines.
Use YYYY-MM-DD-topic.md; append later entries chronologically. Preserve old
entries. Record Finding:, Validation:, and Limits: (use none when measured).
Link evidence and asks rather than copying reports. Keep current status in
the asks ledger and plan index; deferred work needs a tracked queue home.
The journal is the historical record, not another live task list.

The gate requires those three fields in newly added journal lines; changing
only README, a template, a heading or an old file's name does not qualify.
The small-commit exemption is automatic and skips no other check.
No hook creates extra commits.

## Hooks and ownership

Enable once per clone: git config core.hooksPath .githooks

The pre-commit hook prints the proposed paths, checks staged whitespace,
applies the 30-line journal threshold, rejects blobs over 100 MiB, and
checks staged shell/MJS syntax. It honors Git's supplied index, including pathspec and
private indexes. It never stages files or validates a working-tree substitute.
These fast checks are not a full game qualification: typecheck, lint, tests,
played evidence and the third-round ship gate remain the parent's duty.

The commit-msg hook enforces subject syntax/length, a blank line, a
substantive body, Validation:, and valid attribution in the final trailer
block. Placeholders are rejected; when a Codex session ID is present, the
Codex model must match that session's recorded model. Generated messages
must follow the same policy; subject prefixes such as Revert do not
bypass checks. It then runs the markdown-budget guard.
Editorial quality, ownership and truthful evidence remain the parent's review.

The markdown guard refuses more than 40% counted markdown except docs and
design types, including scopes. Evidence, journals and existing asset/archive
exclusions are omitted: mandatory history must not mislabel a small fix.
Choose the type for the actual work; do not relabel features as documentation
just to satisfy the ratio. Keep journal entries short.

The parent commits only owned changes. Inspect the diff and name paths
explicitly; never sweep another worker's index. A pathspec commits whole
files: use a private index for shared-file hunks. Prefer ordinary git commit
with GIT_INDEX_FILE so both hooks run; commit-tree skips hooks and therefore
requires invoking pre-commit and commit-msg explicitly first.
Maintain asks and plans in the same round. Deployment follows AGENTS.md.

Verify hook changes: node --test .githooks/commit-hooks.test.mjs
