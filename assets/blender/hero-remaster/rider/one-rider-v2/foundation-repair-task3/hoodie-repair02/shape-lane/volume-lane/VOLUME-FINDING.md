# Unaccepted sleeve-volume checkpoint

The rounded anatomical centreline transports source radial coordinates with rotation-minimizing frames. It replaces only the normalized arm contribution, scaled by the existing arm ownership. Torso ownership, motion matrices, weights, rest topology, UVs and materials stay fixed.

| Matched pose | Upper strict crossings | Sleeve strict crossings | Upper faces below25% rest area |
|---|---:|---:|---:|
| Single-left neutral elbow90° |74→0|96→0|63→14|
| Bilateral reaching elbow90° |259→105|150→0|84→34|

Upper maximum edge stretch (rest edges at least2mm) improves2.076→1.580× in isolated90° and5.569→5.466× in reaching90°. The former is a volume gain; the latter retains substantial inherited armhole stretch.

All127 sewn cuff aliases and head/hands/gloves arrays remain exact versus matched source skin. Neutral output is exact. Maximum alias discrepancy across11 snapshots is2.50e-16m.

This candidate is not accepted. Current finite crossing tests exclude any shared source corner, so the independent corner category is still required. At120°,59 upper and52 sleeve crossings remain. Four forward/overhead controls are unchanged to2.46e-15m. The rounded garment centreline is approximately12% shorter at90°,34% shorter at120°, while anatomical bone lengths are unchanged. This is not cloth isometry or proof that the arm remains inside the sleeve. Maximum90° correction is81.1mm. Analytic tube Jacobians are not literal triangle or body-contact certificates.

Ready matched render inputs: `skin-single-elbow-90.npz` against `rounded-single-elbow-90.npz`; `skin-elbow-1.npz` against `rounded-elbow-1.npz`. Use actual V7 triangles and identical stored `matrices`. `RoundedSleeve.target(D, posed=None, jacobian=False)` is the offline integration API. No new candidate has been exported or rendered.

Frozen hashes and verified constraints are in `volume-freeze.json`; full finite measurements in `rounded-finite-gates.json`; curve lengths, correction magnitudes and bone-length ratios in `rounded-provenance.json`. The earlier Hermite/full-skin blend and proxy-capsule trials are rejected, retained only as ablation evidence.
