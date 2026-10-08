# One bilateral underarm panel correction

Use the actual compact `fd7761d7` garment as the clothing baseline. Its matched
front/back/profile covers the chest, outer deltoid and upper arm; its failures
are the narrow front axillary wedge and collapsed/jagged rear axilla. The frozen
dense source in working master `9cedbcdb` exposes substantially more chest and
upper arm in front, rear and profile. That placement is an appearance reference,
not an enclosing clothing baseline. These observations do not justify changing
the canonical anatomical body.

The next correction is deliberate cloth-panel authoring, not another fit pass:

1. Select the actual failed `_HOODIE_PATCH` region and adjacent front/back
   armhole-to-upper-sleeve strips. Redraw each local seam perimeter on retained
   front chest, back shoulder, inner upper sleeve, and side panel. Replace the
   pinched patch with one four-sided underarm gusset per side, connected into a
   coherent armhole loop and two supporting upper-arm loops. Do not reuse an
   inside-body boundary merely because its topology is manifold. No fill/grid
   selection retry, tube sweep, projection, OUTSIDE aid, or normal displacement.
2. Author front/rear armhole, inner-sleeve and lower side-panel control points
   explicitly against the actual pectoral, latissimus, deltoid and upper-arm
   landmarks. Begin with 20 mm front/back/lateral cloth ease and an underarm
   fold 20 mm below the anatomical axillary fold; these are artist control
   choices, not proved clearance. Join the controls into a loose cloth panel,
   retaining the selected shoulder seam and visible sleeve fold direction.
   Adjacent derivative vertices may move to make a continuous shoulder/panel
   transition. Do not freeze every historical derivative position or pull the
   entire torso/arm onto the skin. Preserve the selected hood, ribbed hem/cuffs,
   sleeve volume, dropped shoulder character and major folds by feature identity.
3. Record new-panel vertices/faces and moved adjacent vertices. Match the front,
   rear, sleeve and side-panel corners to explicit selected25 source vertex/
   polygon IDs and original UV corners. Preserve existing source attributes
   where valid; mark generated patch defaults as missing lineage. Establish
   separate front/back source-chart correspondence rather than sampling through
   a cavity or reusing invalid generated-patch UVs. Source silhouette/fold
   landmarks guide shape; source coordinates are not sacred fit constraints.
4. Save the editable baseline in the complete private working outfit, displaying
   one actual hoodie and the complete unchanged wearer. Keep the original dense
   source toggleable as an immutable original-PBR reference. Parent compares
   the same compact negative cameras and four full-outfit cameras. After the
   baseline encloses the body and retains selected form, align only the relevant
   original dense panels using the same authored seam controls and transfer the
   actual selected PBR onto coherent new UVs. No generic material substitution.

Exact seam IDs and control coordinates cannot be responsibly chosen from the
available position/weight-only compact array. One minimal readonly extraction
is requested: actual compact polygon/corner-UV/patch/source-attribute arrays and
selected25 polygon/corner-UV/source-attribute arrays. Canonical body geometry,
rest joints and fields already exist in the pinned native-body array. No new
dense generation, fitting experiment, body repair or inventory is needed.

The source-only extractor is `extract_panel_intake.py` with pinned `inputs.json`.
Parent checkpoints it and grants one short serial CPU2 extraction. It opens the
actual compact native, reads the selected25 mesh, writes arrays, and verifies
source/body/rig/target parity. It saves no native and executes no geometry edit.
The resulting exact boundary/control IDs feed the single concrete panel-authoring
source, which must be checkpointed before execution. Baseline shape comes first;
PBR transfer, articulated wearing motion and R0–R5 acceptance remain pending.
