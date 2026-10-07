# Declared cuff-space paths clear the source surface before distal hits

Builder checkpoint only. Exactly one admitted CPU2 array assay ran in 0.921
seconds with exit 0, no warnings or retries. Source08 and source-film41 are byte
unchanged. No render, source edit, fit, skin or further cut occurred.

All 14543 retained source triangles were queried for every one of the 25 fixed
source+Y zero-radius segments. Seventeen have positive computed surface-distance
margin; eight have one strict-interior face intersection each. There are no
tangent/coplanar nearcontacts in this declared family. These are finite path
results, not an occupancy or anatomical enclosure proof.

| Fixed end Y | Paths with surface hits | Minimum positive path margin |
| --- | ---: | ---: |
| -0.655137 | 0/5 | 0.0780025482 |
| -0.305137 | 0/5 | 0.0675871785 |
| -0.105137 | 0/5 | 0.0409649949 |
| 0.145137 | 3/5 | 0.0024091943 |
| 0.245137 | 5/5 | none |

All numbers are uncalibrated donor units. The five first distal hits lie at
source Y 0.08949844, 0.07718911, 0.15684967, 0.23226400 and -0.01927813, with
prototype face IDs 6824, 6064, 7710, 6654 and 6207 respectively. Their full source
vertices, barycentric/UV witnesses and per-corner dense lineage are retained.
None of these hit faces is in either homology cycle's incident neighborhood.
Distal hits can represent ordinary hand/web/finger-front surfaces; they are not
an inferred defect or a removal mask.

The declared paths remain 0.07800 to 0.18453 from the actual cuff boundary and
0.16546 to 0.26442 from the two cycle polylines. Exact closest source-edge IDs and
path/edge witness points are in `probe.json`. This separates the finite path
obstructions from the unresolved cycle feature without interpreting that feature
as a strap or defect.

Frozen-array readback verified all 25 whole-surface distance arrays, intersection
face IDs, source/prototype/UV/dense ancestry and actual boundary/cycle witness
placement. Maximum source-triangle barycentric reconstruction residual is
1.1775693440e-16 donor units. The complete ignored arrays remain pinned for the
parent's independent review.

Limits: Float64 finite geometry, not interval arithmetic. These zero-radius paths
do not establish endpoint solid/void occupancy, entry specifically through the
cuff mouth, a hand-size capsule, general free volume, all palm/web/finger
enclosure, fit or wearable acceptance. The unresolved source genus 1 is not
automatically a defect. Complete calibrated wearer enclosure remains open.
