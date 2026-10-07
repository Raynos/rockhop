# Bottom-edge input mitigation

Finding: Ask331's shared Siri gesture conversation identifies a conflict
between frequently tapped gameplay controls and the iOS bottom edge. End
the touch layer above the safe area plus 20 pixels; keys and HUD hints follow,
while the decorative strip still covers the bottom.

Validation: 24 Chromium/WebKit layout/input cases, 18 touch/orientation unit
tests, 64 actual-game touch checks, typecheck, scoped lint and build pass.
Real-game checks and the
unrelated default menu/map failures are retained in
[the evidence](../../docs/evidence/touch-system-edge-2026-10-07/README.md).

Limits: Physical Siri avoidance requires HR-26. Repo-wide lint fails on
preexisting temporary/rider files. No physics, rider asset or deployment
change; no complete release/device pass claimed.
