Finding: Actual controls02 fails Rookie tick250 at a nearly straight arm;
right forearm affine error is 1.184 mm against the unchanged 0.1 mm bound.
The retained elbow bend is only 0.163 mm while captured segment lengths and
native rest differ by sub-micrometre amounts. Double-precision geometry
shows those small discrepancies can produce roughly 0.1 mm elbow movement.
Exact post-solver mechanism matrices were not retained, so no full cause or
correction is claimed yet.

Finding: One frozen tiny-rig diagnostic replays the original saved controls,
observes before/after IK without modifying solver code, saves the failed
keyed native, then measures reopened IK-on and keyed-FK-only behavior.
The intended correction is explicit standard FK/IK conditioning plus safe
generic-action activation, subject to actual diagnostic precision results.

Validation: Actual first native, failure, conversion and recipe hashes pass
input validation in Python3.9. Two AST tests prove that only read-only
observer calls are inserted and reject changed instrumentation boundaries.
Python AST and shell syntax pass. Parent reviewed source; native job pending.
Evidence: docs/evidence/rider-rebuild/selected-authoring-motion11/gameplay-singularity-source03.json
Ask: 356 and complete-rider continuation under 354.

Limits: No solver fix or native diagnostic has run in this builder round.
Original rest, skin fields, selected appearance and 0.1 mm gates remain
unchanged. FK intervals must be declared as FK; generic original actions
must remain intact with deterministic safe playback copies. Full native10
requires actual qualified provenance, never an invented native08 receipt.
