# Native hand against actual unchanged rubber grip

New nativeL/runtimeR heldshape only. The rejected closing/handle-entry
sequence is not repeated. Original completebody/head/native sources remain
untouched. Source163joint weights articulate fingers; DQS helddelta is a
candidate to bake as a19bone hand morph, not a new runtime finger skeleton.

The recovered actual44triangle rubber grip is transported with a proper
rotation and inverse1.015 authoring scale. Real polygon/taper surfaces replace
the18mm fixture in target projection, signedvertex penalty and diagnostics.
An explicit virtual physics-marker point records the actual rod-axis offset.
Both source shape and virtual marker must transform together in the rig;
marker alignment is not a palm surface contact certificate.

Results: wrist displacement0, hand self-overlapdiagnostic0. Four finger pads
have real surface witnesses0.035–0.109mm away; thumbpad closestgap4.715mm
remains visible.55hand/rod triangle crossing pairs remain; vertexmaximum
penetration0.334mm alone does not bound triangles. Wholetriangle linear
programming against a conservative convex envelope bounds maximum depth
at0.595mm runtime. Quantized/skinny cap planes require at most1.951mm plane
inflation; ALL actualvertices/triangles are inside the measured envelope.
This is conservative penetration evidence, not a zero-intersection claim.

Parent inspected six actual matched PBR/gray closeups. Retain this heldshape
for two-hand/fullrig moving comparison; thumbgap and bland gloves remain.
No accepted playedcontact, closingsequence, complete19rig, otherhand or
normalplayer asset follows from this static appearance diagnostic.

Run build/render via run_cpu.py with isolated2thread Blender and fixed30min
batchdeadline; triangle_audit.py uses installed UniMate .venv NumPy/SciPy
for CPU geometry only. Initial NumPy/Accelerate matmul warnings were replaced
by explicit einsum and strict floating-point errors; final results finite,
maximum unchanged within2e-17m. No installed packages/configuration changed.

Round87 silentproduction baseline passes exact finishbytes/crash103ticks,
restart1msLOW/2msHIGH/errors0. This is historicalproduction health only.
