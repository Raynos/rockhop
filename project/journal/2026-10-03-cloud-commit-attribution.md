# Cloud commit attribution

Finding: User-authorized cloud declarations provide a session-bound explicit
codex:Astra-6 attribution route when local metadata does not exist. Provenance
is user-provided, with exact quote and declaration SHA256, not auto-detected.
Desktop metadata resolution remains the default; invalid cloud input fails closed.

Validation: All59hook tests pass, including desktop metadata and a real
hook-mediated cloud commit. Missing/malformed/foreign/injected declarations and
stale/unstaged provenance fail; actual declared resolver emits exact user label. No hook is disabled and no
session record is copied or invented. Own status hunks exclude concurrent QA.

Limits: The checker validates declared provenance consistency, not independent
model detection. Historical handoff author attribution remains unresolved; its
reviewed checkpoint is already on main. No rider or production asset changed.
Evidence: docs/evidence/cloud-commit-attribution-2026-10-03/README.md.
Ask:256.
