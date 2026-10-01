# Read-only eye reconstruction feasibility

The present head has a thin inner face surface behind its visible face. Cutting
only the visible painted eyes would leave that inner surface in front of fitted
eyeballs. Rebuild each aperture through both surfaces and connect them with a
continuous eyelid tunnel. Preserve the approved head identity and body.

This is a CPU geometry audit and implementation proposal, not a replacement
asset or an appearance acceptance. No model repair was attempted here.

Source: body11 guarded rider, SHA256
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
Source GLB was checked byte-identical after the audit. Recipe:
`assets/blender/hero-remaster/rider/one-rider-v2/eye-strategy01/audit.py`.
Run with existing UniMate Python, `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`.
No Blender/GPU/model execution, package install or production edit occurred.

## Actual source measurements

Head primitive mesh1/primitive0 has 61,099 exported vertices, 49,784 exact
position-welded vertices and 99,485 triangles. It is one connected component
with no nonmanifold canonical edges. Its four existing boundary loops all lie
at the cheek repair regions; there is no pre-existing eye aperture. UV splits
must remain exported splits; geometric welding in this audit is analytical.

The following locations are manually selected source surface seeds, not
anatomical globe centers or a generated landmark detection result. GLB axes
are +X toward the front of the face, +Y up, +Z one side of the face.

| Source eye | Seed Y/Z (m) | Visible face X (m) | Inward face X (m) | Thickness | Back head intersections X (m) |
| --- | --- | --- | --- | --- | --- |
| +Z | 1.6965 / +0.0320 | 0.746970099 | 0.742419726 | 4.550 mm | 0.564122771 / 0.561485878 |
| −Z | 1.6970 / −0.0332 | 0.747949309 | 0.741950141 | 5.999 mm | 0.566383871 / 0.563633338 |

Surface seed separation is 65.2 mm. The inward ray hits have negative X normals
and the visible hits positive X normals. Both eye regions are 100% weighted to
skin joint index4, named `head`; the source skin has the existing 19 joints.
The head mesh uses the current skin, not a new independent head skeleton.

A 26 × 8.5 mm ellipse around each seed, restricted to triangle-centroid X >
0.72 m, selects 463 source triangles per eye. Each mask exposes two degree-two
boundary loops, one outer face and one inward face. +Z loops have 38 outer /
55 inward vertices; −Z 38 outer /57 inward. These counts are evidence about
the source only: they are not accepted cuts or smooth final lid margins.

The front-visible-only mask is worse: it leaves a small extra inner boundary
and therefore cannot be used as a final aperture. Its 174/175-triangle selected
components have 50/43 boundary edges in two loops. Blind visibility selection
or deleting whole triangles would produce incomplete and jagged cuts.

A wider 36 × 18 mm surgical region also has exactly two degree-two loops:

| Region | Source triangles | Outer loop | Inward loop | Entire selected surface X extent |
| --- | --- | --- | --- | --- |
| +Z | 1,229 | 60 vertices | 75 vertices | 0.732718–0.757925 m |
| −Z | 1,185 | 56 vertices | 67 vertices | 0.729830–0.754055 m |

The boundary extrema in `report.json` are boundary measurements, not extrema
of every selected triangle. The displayed X interval above is the union of
those boundary extrema. X > 0.72 m includes both local face sheets and is far
in front of the measured back-head sheets. Do not cut an unrestricted cylinder
through the whole head. Recompute intersections throughout the chosen ellipse
before applying any asset edit, and reject any unexpected third local loop.

## Bounded implementation

1. Start with analytic clipping of a 26 × 8.5 mm ellipse around the seeds above,
   through both face sheets with X >0.72. Preserve all original geometry and
   attributes outside this region. Intersect crossed source edges with the
   ellipse and interpolate original UVs, normals and weights barycentrically.
   Include the arc portions inside a crossed triangle, including triangles
   whose vertices are all outside but whose edges or interiors meet the
   ellipse. A whole-triangle deletion is expressly not the proposed method.
   Use an arc subdivision error at most 0.025 mm, and retain exact source outer
   attributes at the join. Inspect the resulting two loops before proceeding.
2. Connect outer and inward loops with an angular zipper or a shared parameter
   ring so the aperture passes through the entire skin shell. Unequal loop
   vertex counts are normal here. The tunnel must have consistent winding,
   no open rim and no triangles crossing the visible aperture. Taper the lip
   rather than making a thick straight tube. Source normals at the untouched
   rim remain authoritative; use a smooth local normal field for new rings.
3. Fit a fresh installed CC0 eye pair behind that lip. Do not scale the entire
   pair by old MPFB head dimensions. Start with one shared uniform donor scale
   0.0758794548, giving a fitted outer globe radius of 12 mm; translate each
   eye independently to the measured 65.2 mm separation. This common scale
   preserves the cornea/sclera relationship. Map raw donor Z-forward to rider
   X-forward, raw Y-up to rider Y-up and raw X-side to rider −Z-side using a
   proper rotation. Preserve donor UVs and iris placement.
4. A source-apex-aligned initial fit puts donor outer-sphere centers at X
   0.734249 /0.735228 m, Y/Z at the declared source seeds. This is a start,
   not a fit acceptance: raw donor corneal maxZ exceeds its fitted center by
   0.167650 raw units =12.721 mm after the shared scale. Verify actual iris
   front and lid clearance with ray tests and profiles, not a sphere proxy.
   The original inward skin is 4.55–6 mm behind the visible face, so donor
   geometry would otherwise be hidden behind that skin sheet.
5. The tiny ellipse is an insertion-feasibility test. If the surrounding
   sculpted lids remain distorted, move immediately to the measured 36 ×18 mm
   local retopology region, preserving its original front and inward outer
   boundaries. Build 3–4 explicit upper/lower lid rings around an almond
   opening, including canthi, then a tunnel to the inward ring. Preserve brow,
   nose, cheek repair, mouth, ears, neck, hood, clothing, body and all original
   rig nodes. Avoid remeshing or smoothing the whole head.
6. New eyelid skin must not inherit the old painted iris color. Derive local
   skin color from an actual skin boundary band, preserve unchanged atlas
   texels and provide a physical shared-color match at any new UV seam. Keep
   brown iris texture separate. Tune the eye material only to capabilities
   actually supported by the player renderer; a clear cornea layer is not
   mandatory if it sorts incorrectly, and a white spherical overlay is not
   an acceptable substitute for an aperture.
7. Bind new lids and both donor eye layers to the existing `head` joint4 with
   weight1 and the existing skin inverse binds. Preserve all 19 joint nodes,
   clips, body weights, contact metadata, sockets, neck geometry and physics.
   Verify read-only donor/world placement after this binding before replay.

## Stop and acceptance conditions

This is one proposed mechanism with no repair attempts in this audit. Use five
failed attempts to switch mechanism; retain the fifteen-attempt defect ceiling.
If analytic cuts cannot yield exactly two simple paired local loops or zipper
triangulation inverts/folds, switch to the larger bounded orbital retopology
region instead of repeating cut thresholds. If that cannot preserve identity
and seams, propose a fundamentally fresh head-only direction while preserving
the current coherent body and current comparison evidence.

Before visual judgement: canonical skin-surface edges return to the original
boundary count; no new nonmanifold edges; untouched attribute/accessor bytes
remain exact; no open new rim; no degenerate new faces; new head-joint weights
sum1. Eye/globe interiors can overlap intentionally, but front aperture rays
must hit donor eye surfaces before retained inner skin. The lid ring should
cover eye edges without visible floating gaps from front, profile and both
three-quarter views. Verify all of these again under neck movement and riding.

Then judge matched textured/gray closeups and actual played clips against the
mockup target. Parent judges appearance. This audit cannot award a face score,
declare a completed rider, establish the nine-angle checkpoint, or prove
contacts/Garage/motion acceptance.

## Donor provenance and limits

Installed MakeHuman high-poly eyes SHA256
`da2493215b708a344c33dc72f2a9a5b8fa985dcc5a70ad3b208995cf871da8e1`.
OBJ explicitly states CC0 September2020. It contains four connected components
(256+276 vertices per eye), not one generic sphere. A least-squares outer
component sphere has radius0.158145575 raw units, RMS residual0.003532376 and
max absolute residual0.009509855; at the proposed shared scale these are
0.268 mm RMS and0.722 mm max. The inner component radius0.153342858 raw units
has greater residual, so sphere fits are diagnostics rather than a claim of
perfect spherical donor anatomy. Exact measurements, full ray hits, masks,
source face indices, donor fits and skin index names are in `report.json`.
