# Sparse cage section measurement — rejected round152

No model was exported. The point-sampled cage estimator exceeds the unchanged
radius guard on forearm.L:3.3197x.16 or12percent nearest longitudinal points
can undersample angular coverage on the sparse native grid. Parent rejects
this estimator as reliable correspondence; no widened guard or parameter sweep.

[Recorded section profiles and guard](point-section-failure01.json).
An instrumented read-only rerun records the same failure; it is not a second
model attempt. Original fit01/topology/weights/UV and source34 remain untouched.
The initial NumPy vector-matmul warnings were replaced with explicit einsum;
the actual forearm guard failure reproduced. No anatomical or appearance pass.

Next: intersect actual native/source triangles with section planes to measure
connected surface extent, then use one smooth cage fit under the same guard.
No expensive texture bake or generation was run. Ship150passed; next153.
