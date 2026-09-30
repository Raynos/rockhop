# Git hook lint follow-up · 2026-09-30

Finding: The new commit guards passed their own 41 fixtures but broke the
repository-wide lint gate. The subject checker spread a string into code
points, which also counted joined emoji inaccurately; the Node fixture tests
discarded registration promises without an explicit marker.

Validation: The checker now counts grapheme clusters. Added both boundary
cases for a multi-code-point emoji. All 43 hook fixtures and `pnpm lint`
pass; the new index guards still inspect staged blobs.

Limits: These structural checks cannot judge whether a gameplay finding is
true or replace the course, device and release gates.
