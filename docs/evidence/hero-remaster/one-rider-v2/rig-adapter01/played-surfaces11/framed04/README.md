# Current presented-surface evidence, awaiting parent judgment

This capture supersedes initial/framed02 timing and framing diagnostics.
Actual metric vertices are collected after the final camera render. All
480 final skinned hand/sole midpoints project to the screen centre within
1.04e-15 NDC; re-reading the final surfaces changes their midpoint by zero.
The coarse pre-camera world midpoint is recorded separately and is not
used as a current-presentation contact metric.

All 480 physics states, state hashes and rider debug objects exactly match
body09 played01. Same input/source11/19-bone physical pose; lean reaches
both -1/+1, sampled sustained airborne and landing/recovery events retained.

Current movies are `hands/played.mp4` and `feet/played.mp4`, forty seconds
each. Short `maximum-forward`, `maximum-backward` and `landing-recovery`
movies are 2.4 seconds each and mapped to samples/ticks in `events.json`.
All 240 captured frames per view are indexed in `decoded-000` through
`decoded-009.jpg`; original PNGs and float32 metric point masters are
preserved privately at the path in each `frames-archive.json`.

Actual palmar thumb pad gaps remain 4.785 mm right / 4.854 mm left.
Other selected finger pad closest points are 0.024–0.154 mm from literal
rubber grip triangles. Full actual exported glove triangle conservative
convex-envelope depth bounds are 0.595 mm right / 0.799 mm left, including
all-sample drift and float32 allowance. These are not zero-intersection
or anatomy passes. Lowest sole vertex gaps are 0.176 mm left / 0.611 mm
right; nearest-face sign is a local diagnostic, not a full outsole volume.

The source has both 1668-vertex/3312-triangle native hands. Actual GLB
coincident normal/UV aliases require identical skin/morph buffers. Actual
exported physical triangle sets equal native physical triangle sets only
after that validation; final LP uses literal exported indices explicitly.

No art, physics, rig or production camera edits. No visual pass claimed
by the builder: parent must play the clips and consider occluded contacts.
Complete harness typecheck and probe lint pass; headless WebKit errors zero.
Shared locked workload 54.55 seconds, peak anonymous 40.927 GB decimal.
