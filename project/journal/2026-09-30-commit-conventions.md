# Commit conventions — ask 180

Finding: Rockhop's latest 100 commits omit bodies; the existing hook checks
only markdown share. Kami has better prose and attribution conventions,
but its guard accepts malformed placement and ignores subject style.
Wildshard Singleplayer has 88/100 subjects longer than 72 characters and
conflicting live commit recipes. All audited clones use tracked .githooks;
their raw .git/hooks contain only stock samples.

Changes: Add conventional subjects, rationale and validation bodies, final
tool/model attribution, a short round journal, and fast staged-blob checks. Journals are optional below 30 added/deleted
non-journal text lines; placeholder model names are rejected.
Fix the markdown evidence-exclusion bug and scoped docs/design exceptions.

Validation: All 41 hook fixtures pass, including the 29/30-line boundary,
private/pathspec index behavior, staged syntax, final real-model attribution
and exact markdown threshold. Targeted oxlint and shell syntax checks pass.
The local Codex session records gpt-6.1-sol; the resolver returns that model.

Limits: Hooks enforce structure and index checks, not ownership or truthful
gameplay claims. TypeScript/game qualification stays in the round protocol.
No other repository is modified.
