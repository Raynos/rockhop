# R2 read-only construction support

2026-10-03. Root requested one bounded review while the sole integrator's
Blender call was pending. No Blender, model job, construction or source
transfer was performed. These measurements are not art acceptance.

The existing export manifest gives joint distances of 264.937 mm upper arm
and 273.355 mm forearm on both sides, with shoulder joint-origin span
392.147 mm. Six pose OBJ hashes match; each has 15,024 vertices and 27,626
faces. Face order agrees across A/T/neutral. Y-up and Z-up pairs map exactly
as [x,z,-y] at serialized precision. Height is 1.822571978 m and true-T
fingertip mesh span is 1.885454986 m. The short upper arm exists in the
canonical source; it is not an OBJ/GLB-root conversion artifact.

The historical approximate 330 mm target is not independently calibrated
by these artifacts. Adding about 65 mm to each upper arm would add about
130 mm of T reach and alter garment and bike fit. Test one matched-reference
proportion variant; do not treat a length target as visual acceptance.

The retained parity report measures full native weights against exported
four-weight LBS. Body/cloth rest residuals are 0.000936/0.000464 mm, but
raised endpoint maxima are 7.645304/4.715924 mm. Respectively 71 and 10
vertices exceed 1 mm. Asymmetric maxima are 7.003717/4.306993 mm.
The report explicitly flags four-weight export truncation. The OBJ fitting
fixtures already follow exported LBS, not the full-weight native deformation.
These reviewed files omit full native influence lists; discarded weight mass
and exact anatomical locations were not independently measured here.

Establish one source/engine deformation contract before garment polish.
The next implementation test belongs to the sole integrator: make a derived
diagnostic source with at most four normalized influences per vertex, then
export the same body, bind and poses. Compare original native, conditioned
native and actual Three.js export at rest, true action-off A/T/neutral,
forward/raised/asymmetric, riding endpoints and uninterrupted transitions.
Pin complete joint order, binds, root, driver and runtime conditioning;
retain per-vertex displacement and worst-witness IDs.

A proposed diagnostic target is zero conditioned-source/export vertices
above 0.1 mm disagreement. This has not been measured or passed. Plain
top-four trimming can align both sides while reproducing bad deformation;
played silhouette, clearance and bike support are separate judgments.
If quality degrades, deliberately redesign local weights/topology on the
same rig. Root alone accepts proportions and appearance; M0–M5 stay open.

Sources: control01/export-manifest.json and four-weight-parity.json under
anatomical-foundation evidence; control01/references/reference-contract.json
and its six OBJ payloads under anatomical-foundation source. Existing pins
remain unchanged. Coordinator attribution remains unresolved; truthful
reviewer checkpoint is required, not an invented original-writer label.

Root decision at 12:22 UTC accepts the three-way weight diagnostic direction,
not art. Keep measured arm lengths as the control; do not lengthen to the old
uncalibrated 330 mm value. Proposed 0.1 mm is diagnostic only, not a user approval
gate. No generation until the shared fitting contract is actually qualified.
Integrator owns this independent control-weight test after its existing action
clears; generator agreement is not required to begin that authorized diagnostic.

The source/native parity report covers seven authored endpoints. The 193
engine playback samples do not establish continuous source/export agreement.
