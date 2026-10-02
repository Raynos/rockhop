# NEW T-pose proportion and 19-bone adaptation212

Status: **read-only proposal; zero geometry, weights, rig or player changes**.
Parent owns construction admission and visual acceptance. This is one body
direction, not a request to rig all preserved candidates.

Source is the literal finite-cleanup210 mesh, transformed by the explicit211
native-to-game matrix. Every section in `sections.json` includes exact source
edge IDs and interpolation coefficients. `section-summary.json` reports
surface-enclosed area centroids. These are measured clothing surfaces, not
proved hidden skeletal joints. The projection is a geometry diagnostic only.

The source fingertips span 1.39265m against the unchanged liked donor head top
at 1.82257m. Horizontal bind arms cannot be repaired by copying old arm-down
pivots. Provisional shoulder/elbow/wrist section stations give approximately
339–340mm shoulder-to-wrist reach. The target204 reference also shows short
spread arms: manually inspected silhouette width/stature is about .81. It
preserves identity, clothing and clearance; it cannot override movement or
natural anatomy requirements.

`reach.mts` samples the actual deterministic `riderRigFromHips` geometry over
201 interpolated lean values without changing physics. The initial legacy
wrist offset demands up to 609.16mm. `contact_probe.py` then identifies two
literal NEW palm triangle witnesses, measures a source finger direction from
section differences and derives proper anatomical frames. With a declared
downward-finger/forward-palm grip orientation and a17mm rear-wall support
offset, worst demand becomes 560.55mm. This remains an unaccepted contact
hypothesis, not recorded gameplay or an actual cylindrical finger-wrap pass.

One proposed anatomy trial sets upper-arm310mm and forearm275mm, leaving
24.45mm margin against that provisional demand. It moves the source elbow
station from|Z|.34 to about.4896 and wrist from.50 to about.7533. The two
monotone quintic longitudinal increments keep X/Y unchanged, preserve the
shoulder and torso, and translate distal hand shape rigidly. Expected full
span is1.89821m, about1.04 times unchanged head height. `proposal.json` carries
the precise knots, displacements,260mm cap, protected regions and ownership
prerequisites. It does not contain edited vertices or admit construction.

Upper/lower sleeve fold wavelengths stretch about1.93/1.54 times. Numerical
reach cannot accept those resulting folds, shoulder transitions, rest chest
or back. Before any bind, construct exactly one source-ancestry field only
after the parent admits it; freeze literal ownership, prove chest/hood/head
exclusion and hand rigidity, check all triangles/intersections and inspect
actual gray front/profile/back/turntable evidence.

Legs remain unresolved. Surface-based provisional segment lengths total786mm;
legacy ankle demand reaches870mm. With a115mm actual source sole-to-ankle
height and a declared +/-30mm sagittal contact range, conditional demand
still reaches834mm. Actual boot sole/heel/toe witness frames must be measured.
A separately admitted, protected-shoe construction could raise knee35mm and
hip60mm while returning to zero displacement by chestY1.22. That would alter
torso length and therefore requires new spine/hip/shoulder measurements. No
leg field, contact choice, COM or pelvis height changes occur here.

Pelvis rootY.88 is an explicit semantic root20mm below estimated femur-head
heightY.90: the renderer places its root20mm below physical hips. X/Z derive
from theY.90 surface section; hidden femur-head Y/lateral positions remain
estimates. An actual proportion edit must refresh these centres rather than
copying numerical production pivots.

The implementation contract preserves nineteen canonical named bones, the
hierarchy, source identity, physical COM/lean/IK targets, grip/sole sockets,
Garage whole clips and250ms exit blending. Export genuinely oriented bones
(local+Y along each measured segment), fresh inverse binds and a per-side
explicit contact adapter. Existing private hand adapter is insufficient for
new foot target orientation; it currently uses footq0. Both arm and leg
fallback poles need perpendicular projection, scoped to the NEW adapter.

New torso ownership has zero upper-arm/forearm/hand influence. Actual cuff
vertices, aliases and glove-ring weights must remain continuous; sockets do
not repair joins. Head and neck seam aliases share weights, and approved face
geometry/textures remain exact. Targeted morph correctives require actual
standard Three.js parity: Blender Preserve Volume is not an exported guarantee.

The old C19 fixture cannot be retargeted by changing its reference centres.
Regenerate named semantic motions from the NEW oriented hierarchy. Keep NEW
T-pose bind centres in the fixture contract, and distinguish `neutral-bind`
from an authored `neutral-relaxed` arms-down pose. Horizontal, overhead,
forward reach and wrist/elbow controls must move from the freshly authored
relaxed pose and return continuously; T-pose identity matrices cannot stand
in for an arms-down reference. Test bilateral/unilateral controls,48fps,
reverse/halfsteps, gray/PBR and exported Three.js. Corrective morph driving
must be explicit because the current fixture player zeros nongrip morphs.

Later actual recorded RenderFrames must drive the ordinary rider path for
Garage, maximum lean, landings/recovery, saddle/grip/sole contacts and mobile.
None of those gates is passed by the profile reach diagnostics. No 8/10,
game-ready or appearance acceptance is claimed.

Reproduction order: `measure.py`, `contact_probe.py`, `reach.mts`, `propose.py`,
`freeze.py`. Python uses the existing Hunyuan2.1 environment with two CPU
threads; TypeScript runs with `pnpm exec tsx`. No Torch, model job, Metal,
renderer or GPU work occurs. One initial TS relative-import setup failed
before producing evidence and was corrected; the final source is pinned.
