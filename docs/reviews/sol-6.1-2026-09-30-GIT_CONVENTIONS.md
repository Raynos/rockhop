# Git conventions audit — ask 180

Read-only comparison of AGENTS.md, live Git-related Markdown, raw .git/hooks,
effective hooks, and recent commit subjects/bodies. Rockhop changes are in
docs/git/COMMITS.md. Other repositories were not modified.

## Repositories and installed hooks

| Repository | Effective hooks | Raw .git/hooks |
|---|---|---|
| kami-kakushi | pre-commit, commit-msg, pre-push, post-commit | Stock samples only |
| wildshard-singleplayer | pre-commit, pre-push, post-commit | Stock samples only |
| project-wildshard | pre-commit | Stock samples only |
| rockhop, before this round | commit-msg | Stock samples only |

Each clone locally sets core.hooksPath to .githooks. The raw .git/hooks
directory is therefore inactive. Tool hooks in .claude/settings.json and
.codex/hooks.json are separate from Git hooks and do not apply universally.
No games/wildshard directory exists; the user confirmed project-wildshard
is the intended third repository.

## Commit history sample

Samples were taken before this round's changes, including Rockhop at
f2dd04ab. The other heads were ba9930c1, 9dce77bd and cc81afb respectively.

| Repository | Commits | Subjects >72 chars | Empty bodies | Attribution |
|---|---:|---:|---:|---|
| Rockhop | 100 | 0 | 100 | None |
| Kami | 100 | 2 | 1 | Assisted-by in 99 |
| Singleplayer | 100 | 88 | 0 | Co-Authored-By in 100 |
| Project Wildshard | 7 | 0 | 3 | Co-Authored-By in 4 |

Kami's style guide requires 50-character subjects, but 87/100 exceeded 50.
Its commit-msg hook only searches for an attribution-shaped line anywhere.
Fixtures passed invalid subjects, misplaced trailers, missing trailer
separation, and whitespace-only models. Copy its intent-first prose and
tool/model attribution, not its permissive check.

Singleplayer's longest sampled subject was 251 characters; 24 bodies held
only attribution/session trailers. Its stronger bodies explain causal
changes and report measured parity, such as 198d7823's model migration.
Move plan IDs and inventories into bodies rather than overloading subjects.

Project Wildshard deliberately omits commit-msg enforcement, documented in
project/journal/2026-09-12-session-01-scaffold.md. Its coherent-change and
journal rules are useful; it has no enforced subject/body format.

## Workflow findings

- Kami and Project Wildshard require a journal path in each commit. Their
  guards accept template/README-only edits and do not establish a meaningful
  entry. Rockhop checks newly added finding, validation and limits fields.
- Kami's verifier and its nominally staged plan checker read working-tree
  content. In a shared checkout this can differ from the committed tree.
  Rockhop's pre-commit checks read the effective index.
- Singleplayer AGENTS requires explicit pathspec commits, but its live
  docs/SUBAGENT-BRIEF.md recommends staging tracked files and a bare commit,
  with a hardcoded Claude model. Its Codex exit adapter differs again.
- Singleplayer docs/RUNNING.md and its Claude exit skill retain direct
  production-deploy or push-is-deploy instructions. Current AGENTS and
  README use hourly/manual checked deployment.
- Kami and Singleplayer post-commit can automatically commit a bypass
  ledger. Rockhop's one-commit-per-round convention excludes that machinery.
- Tool-level command guards are not universal Git enforcement. A path
  listing makes swept work visible; it cannot establish ownership.
- commit-tree bypasses Git hooks. Rockhop's live exit recipe now prefers
  an ordinary private-index commit or explicitly invokes both hooks.

## Adopted Rockhop subset

Conventional subjects up to 72 characters, a rationale body, Validation:,
and mandatory final Assisted-by: tool:real-model for AI work. Placeholders
are rejected. Codex session metadata resolves and verifies its model.

Pre-commit reports paths, checks staged whitespace and shell/MJS syntax,
rejects blobs over 100 MiB, and requires a meaningful journal entry at
30 or more added/deleted non-journal text lines. Smaller commits are
automatically exempt. Journals and evidence are excluded from markdown
share so a required historical record does not force a false docs type.

No copied 8-second verifier cap, mandatory extra ledger commits, Herdr
integration, reading-queue machinery, or 500-KB screenshot cap. Rockhop
already tracks Blender masters, so Singleplayer's blanket .blend ban would
break this repository's established asset workflow.

Game qualification remains the existing parent-owned round/release protocol.
Structural checks cannot judge an honest finding or prove gameplay quality.
