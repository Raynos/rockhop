# Eased sleeve: actual collision-off/on comparison — unaccepted

A new separately authored local sleeve band replaces the old skin-tight
shirt topology for this experiment. It has288 vertices/528 triangles,
two real24-vertex openings,22mm prescribed radial ease beyond measured
native arm sections, a24-vertex proximal sewn pin ring,24 half pins and
a free distal opening. Canonical body/head/bind and source05 stay frozen.

Rest qualification passes: no body/self triangle contacts;2,400 vertex,
centroid and edge-midpoint samples have minimum unsigned body clearance
20.692mm and minimum local-normal dot18.387mm, exceeding2mm required
separation. The tube radius comes from actual arm triangle/plane sections,
not an iterative gap/density/weight optimizer.

Installed Blender5.2.1 LTS runs49 sequential24Hz frames over two seconds
to the original bike-free FK112 bend. It consumes an animated full-body
Collision modifier after deformation and cloth body/self collision,
quality8, cloth/self distance1mm. Native RNA settings are frozen in
engine-handoff.json. The official [Collision documentation](https://docs.blender.org/manual/en/5.2/physics/collision.html)
describes collider participation and modifier ordering; actual installed
settings and measured response take precedence over generic advice.

| Outcome | Skin only | Cloth collision off | Cloth collision on |
| --- | ---: | ---: | ---: |
| Final body triangle pairs | 0 | 257 | 0 |
| Final nonadjacent self pairs | 0 | 443 | 0 |
| Worst sampled local-normal dot | 12.684mm | −40.836mm | 0.346mm |

Both cloth variants have exactly equal initial vertices, identical49
kinematic body frames, pins, mass, stiffness and timing. Only object/self
collision toggles change. Their maximum vertex difference reaches277.036mm.
Collision-on has zero body/self triangle contacts at every measured frame.
Native simulation costs6.84s on and5.26s off with one CPU thread; these
are offline timings, not game frame costs or a mobile pass.

The on-run sampled clearance floor0.346mm is below its requested1mm
cloth distance. Zero triangle contact counts do not certify every thickness
target or complete signed-volume clearance. No universal no-clipping claim.

The continuous front/rear played receipt compares identical neutral fabric
in skin-only/off/on columns, with every raw simulation frame shown and
playback slowed2×. Rendering uses immutable baked vertex streams, so
presentation does not resimulate or alter the comparison. The parent judges
folds and fabric behavior; this is a local response test, not final clothing.

The rest GLB has300 rows (12 UV seam duplicates),528 triangles and the
exact original51 joint hierarchy/inverse binds. ActualGLTFLoader rest
versus native error is at most0.000599mm. export-ancestry.json maps every
exported row/triangle to native pattern IDs, anchors and weights.

Blender collision response is **not automatically exported in glTF**.
Agent3 must consume live body colliders in an explicit bounded response,
verify relevant self/inter-garment handling, and play matched collision-off/on
actual game poses with mobile costs. A few baked keys cannot establish
safety for arbitrary game poses. engine-handoff.json provides current
rest topology, anchors, edge constraints, body arm geometry/skin and actual
native settings, while keeping that live-engine gate open.

Human/root rejection of hoodie, jeans and partial footwear remains. Jeans
need hip/knee ease and deformation; new shoes require complete uppers,
soles, heel/toe enclosure and real ankle openings. No recoloring/registration
substitutes for wearable volume. The useful Garage mannequin and protected
body/head/bind remain the baseline. No normal player asset changes.

The parent-relayed Ask279 live-collision clarification is narrowly reviewed
by native Agent1 in this source/evidence checkpoint. The original bridge
writer's execution identity remains unresolved; the commit reviewer uses
the active session's resolved attribution.
