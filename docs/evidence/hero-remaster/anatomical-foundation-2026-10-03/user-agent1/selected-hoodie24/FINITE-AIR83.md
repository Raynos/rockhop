# Four finite fitted-native air corridors — unaccepted

The exact source24 polylines from cuffs/hem/neck to common native chest
have positive minimum distances to every saved garment triangle:

| Path | Minimum distance | Radius after numerical0.0001mm margin |
| --- | --- | --- |
| Right cuff |23.640348mm |23.640248mm |
| Left cuff |35.006991mm |35.006891mm |
| Hem→chest |52.200801mm |52.200701mm |
| Chest→neck/head |52.200801mm |52.200701mm |

These are registered canonical Blender metres. Original donor handoff
c766db59… remains separately pinned and uses uncalibrated generation units;
its values are not wearer metres. Original extra nested hood walls and
unresolved outer-torso branch remain explicit, no wall deletion.

Reuse Agent2's committed f29ef741 exhaustive segment-edge/endpoint-triangle
implementation SHA199bf90f… unchanged. It conservatively bounds all24,359
triangles by AABB distance and tests every candidate beneath a real vertex
upper bound. Rerun annular/rotated-translated tube analytic controls pass
within1e-10; intersecting cap and coplanar ambiguity refuse clear proof.
Initial pin came from an earlier recipe receipt; mismatch failed before
native load. Committed f29ef741 blob verified equal to working recipe and
then pinned, no blind mutable-file acceptance.

A positive-radius connected neighbourhood of each specified polyline
misses garment material walls. This is stronger than zero-width paths and
free-edge counts, but not full anatomical capsules/body coverage, physical
fabric thickness/ease or formal interval certification. Native24 remains
0body/0self; no source save/capture/rig/motion/body-head-51bind mutation,
Library/player promotion or playedart/M0–M5/mobile acceptance.
