# One registered local shell200 trial

`run.py` starts from unchanged source185 and refuses existing attempts.
It runs the one `solve.py` and final Float32 `verify.py`; no retry is permitted.
Authority: `docs/evidence/hero-remaster/one-rider-v2/local-shell199/parent-construction-contract200.json`.

The only algorithm change from199 is line-search acceptance. The native CCD
cap is an upper bound. A false continuous recheck rejects and halves that
proposal within the same initial-plus30-halvings budget; only CCD, finite
energy, valid area and Armijo together accept a proposal. Every proposal is
logged. `acceptance-rule.diff` shows the complete acceptance-only change after
normalizing round-status labels. Objective, coefficients, source stations,
46/138 freeXYZ domain,168 source incidence,78 boundary,88 source row aliases,
Jacobian, Hessian, damping, collision settings and stopping bounds are unchanged.

The indexed private `construction.npz` is the sole final actual candidate.
`trace.npz` stores initial and accepted internal states, not extra character
outputs. `audit_trace.py` verifies all accepted segments with unfiltered
all-five CCD, checks proposal acceptance logs and the final actual Float32
surface without accepting an update or modifying geometry. The target/root
rejection prevents GLB export. No GPU, rig, player asset or shared doc is changed.

Evidence: `docs/evidence/hero-remaster/one-rider-v2/local-shell200/`.
