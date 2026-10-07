# Native target and complete selected-source surface charts

This checkpoint prepares actual target and source geometry for the next fit.
Neither dataset is a glove candidate or a visual acceptance.

The frozen combined04 RiderBody primitive covers all 10,582 native source IDs.
Every duplicated exported position agrees exactly after the declared conversion
from glTF to native coordinates `[x, -z, y]`. Body faces are recovered through
those IDs. The exported skin array supplies the exact order of 75 joint names;
all coefficients come from rig04 `weights-four.json`, rather than the exported
GLB's thresholded and renormalized weights. Independent readback compares every
named native coefficient for exact equality.

The original rig04 rest record contains 404 control/deformation bones; the
frozen contract and GLB select the same 75 exported names. Hand, forearm, palm
and digit rest comparisons have maximum head/tail residual 5.9605e-8 metres and
matrix-element residual 5.9605e-7 from native float reconstruction. This is a
measured tolerance comparison, not byte equality of the rest JSON files.

Each complete hand has 763 vertices, 1,484 triangles, Euler characteristic one
and one 40-edge cuff loop, cut exactly 28 mm proximal to its wrist. Intersections
share source-edge identities. Every triangle corner retains source body triangle
and barycentric ancestry; reconstruction error is at most 1.25e-16 metres.
The cuff-plane residual is at most 1.06e-16 metres. All 15 phalanx fields are
present on each hand. Original and clipped seam coefficients preserve exact
native coefficients or their declared linear interpolation; this input needs no
new four-influence truncation. These hand surfaces supply containment, cavity
and field references only, never the glove exterior.

The source chart dataset retains all 7,306 referenced cavity08 vertices and
14,543 faces. Every face has one primary patch; 19 patches include five distal
digits, five full mixed collars, four web regions, two palm sides, palm rim,
cuff and the protected cuff feature. All 427 mixed palm/digit triangles remain.
The 1,050 chart seam edges use the same original vertex identities on both
sides. A 239-face neighborhood protects the certified cuff cycles and two mesh
rings; no cut, repair, replacement or source coordinate change occurred.

Positive graph harmonic coordinates extend the five distal regions and actual
cuff boundary over the complete selected surface. Partition unity residual is
5.996e-15. These are source interpolation coordinates, **not skinning weights**.
Each digit also has exact source arc, transported angular frame, radius and
terminal axial residual coordinates. The independent inverse reconstructs all
source points within 1e-12 donor units. Source XYZ, retained faces, prototype
corner UV and dense triangle/barycentric ancestry remain exactly unchanged.

The geometric atlas operates on the original 3D surface. It does not claim a
bijective 2D flattening, manufacture replacement texture coordinates, or require
the cuff handle to be a disk. Web/palm/cuff patch ownership is an explicit
fitting hypothesis; the source UV authority remains the original dense corners.

Validation: target extraction, source atlas preparation and independent readback
each pass under `-W error`, exit 0, in under one second per command. Readback
checks pinned inputs, every native coefficient, source geometry/material ancestry,
single cuff loops, all 15 segment fields per hand and coordinate reconstruction.
See `target01/target-extraction.json`, `atlas01/source-atlas.json` and
`preparation-validation.json` for measured values and exact file pins.

Limits: no target correspondence, deformed distortion, complete enclosure,
source fit, dense appearance transfer, native assembly or played art pass is
claimed. The next bounded fit must operate on this actual selected exterior,
with shared source seams, direction-complete constraints and measured distortion.
