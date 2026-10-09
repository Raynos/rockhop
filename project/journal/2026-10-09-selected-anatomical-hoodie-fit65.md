# Resolve the actual anatomical cage system before another native run

Finding: Actual64 reached all native anatomical targets, then stopped before raw save
because its normal-equation cage solve left2.554mm interpolation error. It did
not save the exact target arrays. The65 diagnosis reconstructs all656 controls
from the pinned complete60 CPU target report and explicitly preserves that
provenance; it does not claim those are unobserved exact native64 targets.

All656 source controls are distinct. The40mm cubic interpolation matrix is full
row rank, but solving its squared Gram matrix drops13 modes and leaves0.728mm
error on these CPU controls. Direct least squares retains all modes and reduces
error to1.01e-11m. A complete direct-only CPU continuation still fails: enormous
coarse coefficients give a484586 derivative bound, so the unchanged0.85 bound
permits almost no movement in64 steps. That failed candidate is retained.

Constructor65 combines the original40mm coarse basis with a sparse fine basis
whose spacing is the smallest actual original paired-wall span,2.883918173mm
in the CPU controls. The coarse basis carries broad displacement; the fine basis
resolves the paired anatomical correspondence. Both use direct least squares.
Implicit zero coefficients avoid a large fine tensor allocation. Exact adjacent
coefficient differences bound each level; summed column bounds certify the shared
C2 field globally. The existing0.85 per-map limit and64-step ceiling are unchanged.
Boundary coefficient layers are fixed exactly at zero during solving.

The complete656-control CPU solve and serialized replay pass in27.554s:28 maps,
maximum endpoint error2.78e-17m, all rows retained at every solve. The all-pair
displacement slope lower bound is1.829, consistent with needing composition rather
than one0.85-bounded displacement map. Full-source bounds were used, but the full
716971-vertex cloth was not transported or accepted in this CPU preflight.

Validation: 21 parent-reproduced fixture groups pass, including exact sparse/dense positions,
Jacobians and derivative certificates, compact zero extension, paired controls,
unchanged64 anatomical targets/clearance policy, exact saved-map replay and
source lifecycle pins. Nominal2.6mm clearance and existing20µm measurement
tolerance remain unchanged. No parameter sweep, source-point removal or endpoint
tolerance change was used.

Native65 saves exact material target arrays and their report before cage solving,
so a solver failure is directly reproducible. The native save still precedes
expensive postconstruction qualification, followed by independent reopen. Source
identity, UV/PBR, named fields, both source sheets, exact75/full reference and
glove41 gates remain mandatory. Registration implementation is `multiscale.py`;
`cage.py` remains the explicitly failed direct-only CPU diagnostic.

Limits: No Blender/native job or commit was launched by this builder. Source65 is an
unaccepted construction candidate. Parent guarded full cloth transport, saved
contact/tangent qualification, distal integration and played rider review remain.
