# The selected exterior supports complete sampled finger contours

This is a source-only checkpoint, not an accepted glove. The failed normal-ray
reconstruction did not establish that the selected glove lacks finger geometry.
The new recipe preserves actual source triangle/edge identities and examines
complete cross-section contours before any semantic triangle filtering.

All 20 source section-center planes have a selected closed contour with degree
two at every contour node. All 360 sampled radial directions per contour hit
exactly once: 7,200 directions, no missing or multiple hits. The source triangle,
corner barycentrics and radius for each hit are saved in
`source-section-witnesses.npz`; `source-measurements.json` pins all inputs.
These finite samples support a section/angle construction method; they do not
prove unsampled sections, fit, enclosure, source anatomy or visual acceptance.

The previous pure-label intersection trees omit 427 mixed palm/digit triangles.
Their labels were originally qualified only as distal connectivity, explicitly
excluding proximal roots and webs. Source chart boundaries therefore cannot be
borrowed from skinning-weight thresholds or treated as missing donor geometry.
Two-axis maximum radii and farthest hand-normal hits are retired for construction.

The exact cavity08 candidate remains usable for the next source-chart analysis:
all 8,000 stored source coordinate rows and its 14,543 retained triangle rows
match the original compact selected exterior. There are 7,306 referenced
vertices, 21,850 edges, one 71-edge boundary, no nonmanifold edges, and Euler
characteristic -1. The original source UV and dense ancestry remain available.
Its existing aperture still needs measured target-wrist correspondence.

Correction: the certified genus-one cycle neighborhoods are near the **cuff**,
not the palm. Cavity09's exact cycle witnesses and cavity10's played-context
record allow a possible legitimate cuff strap/detail. Neither genus nor a
desired hand-shell Euler number authorizes its deletion. Preserve the feature
and leave its appearance interpretation to the parent.

Validation: the deterministic NumPy-only assay completes in under one second.
The first run emitted host BLAS floating-point warnings at matrix multiplication;
explicit finite-checked reductions replaced that operation. The same assay then
completed with `-W error`, exit 0 and unchanged measured outcomes. No Blender,
model, browser, fitted mesh, native checkpoint, bake or player asset was created.

Limits: selected source section centers are geometric hypotheses rather than
annotated joints or tips. Original dense corner UV and detail transfer, complete
source chart coverage, seams, deformed surface enclosure and moving appearance
remain pending. The parent owns all played art judgments.
