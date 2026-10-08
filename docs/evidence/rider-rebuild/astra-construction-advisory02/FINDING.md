# Construct surface regions; stop making details gate the outfit

Independent focused advisory, 2026-10-07; Codex / gpt-6-astra, high.
Read-only production inspection plus cheap array replay; no Blender job, source
edit, bake, export, commit or art acceptance. Parent owns the construction lease
and judges played results. R0–R5 remain open.

**Keep the current wearer/shared75 foundation. Replace the glove's ray-stamped
panels with deliberately selected, inset/extruded surface regions. Rebuild the
boot forefoot and its sole perimeter locally around the actual foot outline.
Assemble those with the saved jeans and selected25 hoodie in one native scene
before more isolated detail work.** This is specific mesh construction, not a
new fitting solver, a fresh body restart or a generic replacement outfit.

## The actual blocker is now identifiable

I viewed all four actual `production-boots01/authored02` PNGs: dense lateral,
dense toe-threequarter, derivative lateral, derivative toe-threequarter. Both
actual dense and simplified versions expose the same outer toe. Both have a tall,
flat-fronted toe box. The selected heel, outsole, laces, tongue and collar remain
recognizable. Thus this is an authored fit/silhouette failure already present in
the high source; a new UV atlas or higher-resolution bake cannot correct it.
This is a negative rest finding, not movement judgment.

The script's lattice lifts the forefoot vertically, with width scaled uniformly
about the source width origin at each longitudinal station. The physical outsole
rows are held vertically; toe, ball, instep and sole edge are not individually
modeled surface regions. The result adds excessive vertical volume without
fitting the asymmetric toe footprint. This diagnosis does not establish that
feet need rebuilding. The unchanged body remains a valid construction reference.

I replayed the glove author02 failed sample using the actual small hand/body NPZ
arrays, its current ease calculation, finger controls and triangle intersections.
The error point is **thumb / first panel / row 0 / column 4**, matching the log
within 2.44e-9m. It is not another pinky failure:

| Actual ray result | Consequence |
| --- | --- |
| Full scaffold face279, hit18.73897mm, outward dot+0.98880, seeds[-1,-1,-1] | Valid outward surface exists, but isolated-tip ownership excludes it. |
| Face283, hit43.04645mm, outward dot−0.96647, seeds[4,-1,-1] | Own-thumb support retains only the exit face here; facing rejection follows. |

`sourceHandBranchSeeds` labels isolated distal geometry. The author uses it to
own proximal panel surfaces, while locating those panels by bone-chain distance.
The thumb-root surface crosses the unlabeled thenar/web region. This fails even
when the hand has usable surface geometry. Neither a missing-ray exception nor
this filtered exit establishes broken anatomy, bad bones or reversed body normals.
Do not flip normals or relax the facing test to make this control pass.

Current native verification independently reopened the75 rest records, exported
skin and measured small digit movements. It explicitly leaves moving anatomy
open, including proximal pinky weighting. Keep that limitation. It is not a reason
to discard the whole foundation or another excuse to certify it before clothes.

The current glove also appends every feature to Python arrays, creating the mesh
only after all panels, ribs and the cuff succeed. One decorative panel destroys
the entire deliverable. `save_checkpoint` is reached only after both complete
hands. This architecture, rather than expensive computation, explains why the
3.524second failure leaves no editable gloves.

## Latest jeans and hoodie evidence

I also viewed jeansauthor03 fit-review01 front, back and profile PNGs. Skin breaks
through the front saddle, buttocks, inner thigh and posterior knees/calves. Reject
before baking. The broad selected-donor Shrinkwrap blend is0.78, pulling the new
shell toward an inadequately fitted sculpt. The central crotch is already excluded
by abs(x)<.065 and z>.72, so projection alone cannot explain all exposure.

Use the jeans' one targeted shape repair: make the unchanged body the fit boundary.
Disable selected-sculpt projection on pelvis/saddle and affected knee/calf panels;
move/enlarge authored pelvis/crotch and leg rings around the actual wearer. Keep
selected folds on useful exterior regions. A stock regional OUTSIDE_SURFACE
finishing Shrinkwrap may push remaining penetrating leg/pelvis vertices outward
while preserving already-loose surfaces. Treat it as an ordinary modeling aid.
Do not globally wrap the saddle: nearest-body attachment near inner thighs and
the concave crotch may choose the wrong wall and cannot design crotch ease.
Author the bridge directly, then inspect the same three views before baking.

Hoodieauthor01 now fails its selected-face quad assertion after Grid Fill. The
actual log/receipt records pre-patch native f9606142 saved and exit1 after1.747s.
Existing selected boundary-adjacent triangles may contaminate selection-based
new-face bookkeeping. That is plausible, not proven malformed new topology.
Track actual created faces using preexisting face tags or BMesh created-face
output, then inspect the patch. Preserve and review the saved fitted hoodie.

## One conventional construction route

**Use one common native assembly and direct mesh-region authoring.** Retain the
selected dense donors as material/sculpt sources and untouched originals. Save
editable garment objects before ornaments and bakes, with failure status where
needed. Those are private work in progress, never qualified player assets.

1. **Boot forefoot:** reopen the saved authored02 source. In actual foot-local
   top and side views, draw the toe perimeter around the visible five-toe surface,
   the ball section, instep section and plantar plane. Keep the selected heel,
   quarters, tongue, laces and collar. Cut the malformed front upper at a deliberate
   seam/section behind the toe box and rebuild a small quad patch with a rounded
   toe cap, toe-side walls and a lower vamp. Shape the matching outsole edge to
   that same footprint. Do not retain the old narrow sole perimeter and merely
   inflate the upper. Keep selected sole thickness/tread and a predominantly
   foot-rigid weight field. Use the intact selected upper/sole maps and fit their
   dense local source to these sections for a local detail bake. Check both feet;
   do not assume the mirrored right shape fits the left unchanged.
2. **Glove shell and panels:** save the existing tailored anatomical shell as an
   editable starting mesh immediately. In the actual shell, select connected
   dorsal finger regions and an explicit thumb/thenar region; selections are
   authored surface regions, not thresholded skin weights or tip labels. Shape
   their boundaries to the selected glove's seam/pad outlines. Duplicate/inset
   and raise those faces locally for the leather panels, or extrude their interior
   with the perimeter held. Add subdivision/support loops as necessary. Derive
   seam curves and joint ribs from actual selected mesh edges, so they already
   lie on the glove. Apply this to ALL pads and ribs, including palm, back,
   knuckles and cuff; no nearest/ray fallback placement. The thumb root includes
   the proximal surface
   represented by face279; do not blindly copy that one face ID as a whole region.
   Retain/sculpt the selected broad curved knuckle pad, narrow finger pads, ribbed
   joints and cuff closure. The nine-by-nine generic domed rectangle everywhere
   is insufficient to claim the selected glove shape. Save after shell, after each
   hand's authored features, and before material transfer; errors retain work.
3. **Selected appearance:** use each current real dense material source. Fit the
   selected dense panel/detail regions to the corresponding authored surface with
   explicit control-point/proportional edits. Bake corresponding regions in
   isolation: palm, dorsum, each finger and cuff; upper/sole for boots. The existing
   glove bake's whole-hand15mm normal cage can reach neighboring fingers and
   opposite surfaces, so do not assume it transfers the selected stitched design
   correctly merely because it writes textures. An early1024px real-map bake can
   prove alignment; preserve the4096 originals and produce final master maps once
   alignment works. A black material or invented generic stitch pattern does not
   substitute for selected appearance. Keep silhouette folds/pads in geometry.
4. **Finish assembly immediately:** append the actual saved jeansauthor03 and
   hoodie25-derived fitted objects to that same shared75 master. Apply the bounded
   jeans repair above before baking. Correct hoodie new-face bookkeeping and
   inspect its actual patch; preserve hood/torso/folds. Check jeans cuffs over
   the actual rebuilt boot collars and hoodie cuffs over the actual glove cuffs.
   Fit decisions happen with adjacent garments present. Keep the full body visible
   for diagnostics; no hidden feet/legs or geometry removal to conceal exposure.
5. **Skin and play that outfit:** retain compatible semantic fields; author only
   the changed regions' transitions. Play neutral→reach→crouch→standing ride→seated
   ride→return, including close hands/hips/shoulders and both side profiles. Export
   the identical candidate through the existing private adapter, and play Garage
   and a short silent actual game ride/crash/restart. A successful rest fit grants
   no art acceptance. Diagnose new motion defects on this dressed result.

This does not mean another generic glove shell becomes the product. The shell
is a scaffold. Selected seam boundaries, padded silhouette, cuff/strap and actual
leather/material transfer must be present in the first complete textured review.
If those cannot be authored, say so instead of calling source pins equivalent art.

## Bounded next work and stop conditions

Use the next construction block for **one local boot forefoot replacement and one
surface-region glove pass**, saving editable objects early. This is the topology
replacement required after the consumed shape-repair budget, not author03 of the
same ray/lattice mechanism under a new name. No new registration/chart/fit-cert
framework, no more universal clearance offsets, no new body/rig/AI generation.

Before any expensive bake, inspect the combined native rest model in front, back,
both profiles and close hands/feet. These checks can reject gross exposure,
malformed silhouette or lost selected features. They cannot accept moving art.
Proceed to one quick actual selected-material transfer and complete outfit film;
do not finish every isolated family's entire validation campaign first.

After this one construction block, require a saved complete editable outfit or a
plain report of the specific art task the agents cannot perform. At most one
local repair may address an observed defect of the newly rebuilt surface; no
new projection scheme. If usable selected pads/toe box still cannot be modeled,
prepare the exact current wearer, rig, selected donors/maps and failed comparison
views for a character artist. Autonomous coding does not guarantee character
sculpting skill. Do not spend another day substituting authoring scripts and
provenance checkpoints for a fitted textured person.

The existing exact native/GLB/GPU, contact/reset, device and release gates remain.
Run them on this concrete candidate; no normal-player promotion while unfinished.
The next credible progress report is the dressed native/engine moving result,
not an assertion that a high-resolution source was successfully saved.

## Inspection scope

Read current plan, prior advisory, four garment author scripts, boot controls,
actual guard02 glove log, native02 independent verification, and jeansauthor03
receipt. Viewed the selected glove reference, all four bootauthored02 images and
three jeansauthor03 rest views. Read the hoodieauthor01 failure log/receipt.
Ran only small NumPy array calculations, with Blender's bundled Python, to
identify the exact failed thumb sample and its two intersected triangles.
No films were played; no art score or anatomy qualification is awarded. Official
Blender manual lookups failed in the web tool (402); this report does not pretend
new external research succeeded. Prior advisory retains its official references.

The exact read-only replay is replay-thumb-failure.py. Hand triangle279 uses
vertices[318,690,689]; triangle283 uses[322,686,685]. These are author02 thumb
observations, distinct from the previous guard01 pinky diagnosis.
