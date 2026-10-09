# Exact cuff attribution and local source construction

All three parent-selected fixed-pronation endpoint rays hit a front-facing
selected glove in front of a front-facing hoodie. These are real garment
intersections, not missing hoodie faces or a material/shadow artifact.

`diagnostic02.json` reconstructs those triangles from exact decoded585ae
source fields and the recorded native75 pose. It also verifies the full
wearer wrist Basis and named native fields against their original source.

- Left167304: 0.060–0.725 mm outside the nearest sleeve surface at rest and
  0.061–0.725 mm played. Both layers use the identical distal forearm.
- Right74724: 1.613–2.063 mm outside at rest, 1.621–2.073 mm played. Its native
  field matches the actual wearer. Common-field replacement changes only
  0.008–0.009 mm; this is substantially a rest fit problem.
- Right81481: 0.633–0.838 mm outside at rest, 1.339–1.548 mm played. It lies
  0.815–1.980 mm distal to the native wrist. Its hand/palm field differs from
  the nearby canonical wearer. That difference can move it by3.6–3.8 mm.

All nine selected glove vertices remain5.0–6.5 mm from the real wearer. These
measurements do not authorize shrinking the glove or replacing its already
solved palm/finger fields.

The prepared `fit.py` keeps every glove and every native field exact. It
uses the source sleeve's real layered geometry and native distal forearm/
wrist carrier, constraining all cuff vertices against the actual glove
outer envelope through both241-pose played sequences. A connected Dirichlet
obstacle solve propagates the minimal required outward correction across
that cuff domain; the remainder of the hoodie is fixed. Fabric layer spacing
comes from the selected sleeve itself. The numerical clearance floor derives
from the source float32 ULP, rather than a fitted artistic offset.

Validation: guarded extraction and diagnosis pass; constructor syntax passes.
The constructor has not executed. Finite ray constraints are not exhaustive
triangle containment and cannot substitute for the parent's new moving clips.
