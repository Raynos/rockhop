# Wardrobe audit before rider agent2 construction

Read-only audit, 2026-10-07. No art acceptance, new experiment, Blender load,
source edit, fit, skin, bake, inference or player promotion. Parent alone judges
played clips. Window: October2–7; review includes the October5 independent audit,
current finish plan, October7 handoff, selected-hoodie24/25/26 and every current
finish wardrobe finding. `commit-window.txt` records the relevant dated history.

**Finding:** the appearance sources are intact and reusable. Wearable construction
is unfinished. Further cuff rays, homology proofs or ambient fitting retries will
not produce the complete outfit. Preserve the selected appearance, deliberately
construct hand/foot/leg garments around the exact wearer, and replace spatially
ambiguous hoodie attachment with continuous semantic fields.

## Exact retained source costs and available construction inputs

`source-readback.json` freshly rehashes originals, cleaned donors, maps and
prototype NPZs. All four originals, all16 prepared donor/map/prototype pins and
all three native hoodie pins match existing receipts. GLB JSON independently
confirms the old zero-skin/zero-animation claims and triangle totals.

| Original | GLB bytes | Triangles | Prepared prototype |
| --- | ---: | ---: | ---: |
| Hoodie paint06 `800d7a97…` | 42,329,320 | 921,722 | 9,968 vertices / 20,000 triangles |
| Jeans `7dbec82f…` | 43,271,320 | 841,998 | 7,978 / 16,000 |
| Single glove `890f8693…` | 22,940,908 | 570,242 | 8,000 / 16,000 |
| Single boot `b8dbd980…` | 32,387,936 | 611,198 | 4,986 / 10,000 |
| Total unique sources | 140,929,484 | 2,945,160 | 64,000 prototype triangles |

The64k prototype sum is not a dressed-pair cost: duplicated glove and boot
prototypes make88k outfit triangles before body/head, before source24 hoodie
substitution and before inner shell/rim geometry. No phone cost acceptance exists.

Reusable production inputs live in ignored
`assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/`:
cleaned donor vertices/faces, exact retained original triangle rows, original
**corner** UVs, byte-extracted4096 base-color/MR PNGs, provisional prototype
barycentrics and correspondence recipes. `prepare.py` performs explicit derivative
cleanup; it does not repair intersections/openings or create joint loops.
`register.py` supplies coarse semantic placement, not a completed fit.

Do reuse exact donor corner UV/map lineage, proper source basis and explicit
mirrored winding. Do not adopt prototype per-vertex UV projection as final UV:
one vertex can straddle distinct original UV corners. Correspondence uses32
nearest centroids, which is a bounded candidate search, not globally certified
closest surface. Final chart bake needs explicit semantic surface ownership,
dense triangle ID + corner barycentrics, seam padding and channel conventions.
There is no original NORMAL attribute in these four GLBs: derived normals must
be labeled as derived. No final seam-aware bake or joint-looped garment is ready.

## Hoodie24/25/26: keep the appearance, repair actual attachment

- Source24 has12,430 vertices /24,359 triangles and579 free-boundary vertices.
  Compact dilation changes549 vertices by at most11.473mm while preserving all
  free-boundary positions, polygon/UV/PBR data; old logical-body/self rest counts0
  do not include its protected-head crossings. Its local master rehashes exact.
- Source25 changes only crease shading: all19,878 faces smooth,2,671 edges sharp
  at30degrees;64,115 reopened corner normals match the selected treatment.
  Parent previously accepted the rest silhouette for bounded qualification and
  selected this shading. This is not moving9/10 or whole-outfit acceptance.
- Source26 attaches the donor through the unchanged1,250-vertex structural cage.
  468 donor vertices lose fifth/sixth weights; maximum removed mass1.4395%.
  The actual529-sample native sweep fails FULL and FOUR equally at peak959
  logical-body /4,095 native self contacts. Maximum FULL/FOUR loss4.113843mm is
  near hood/neck; elbow loss0. Truncation is not the principal attachment cause.
- All three have490 rest head-crossing pairs on93 garment triangles /88 garment
  vertices at rear lower-neck/head. This geometry failure predates skinning and
  shading. All24 coverage misses and irregular cuffs remain unresolved.

Specific field cause comes from `selected-hoodie26/attachment95/FINDING.md`:
149 lowest-boundary vertices average33.713% thigh influence; maximum46.388%.
A preserved analytic boundary-only thigh-to-pelvis transfer reduces squat hem
nonplanarity19.844mm to0.255mm, but was never authored/admitted as a candidate.
At the right elbow an actual edge shrinks to31.499% despite81.944% mean-blend
length; neighboring weights differ by L1 up to1.153 and cage anchor jumps reach
2.750 material-edge lengths. Shoulder edge ratios0.022..7.918 likewise reveal
attachment discontinuity plus affine compression. Full/four mass tuning cannot
fix these spatially varying fields.

**Bounded hoodie change after foundation review:** clone source25 in a new leaf,
keep its geometry/UV/PBR/crease normals and define explicit skirt/hem panel IDs
from actual boundary/adjacency. Author pelvis/chest field through that panel,
with a continuous transition to existing waist fields and zero thigh influence
on the149 lowest rows. Preserve other fields first; retain source26 FULL/FOUR as
failed controls. Measure saved/reopened normalized FOUR and retained FULL on the
same exact old squat/reversal and held-out hip motion. Include adjacent rows,
all head/body/self/inter-layer targets and the unchanged24 coverage witnesses.
This tests a diagnosed authoring correction; it is not another global projection.
It alone cannot qualify shoulder/elbow attachment or collar clearance. Subsequent
semantic sleeve/shoulder partition and scoped collar geometry are separate units.

## Gloves: current diagnostic opening is not the production glove

Original donor has a blind inner cuff roof in both dense and simplified geometry.
A smooth ambient bijection cannot create a new passage. Fit01 branch-wise warps
introduce2,262 R self crossings and fragment under curl; fit02 smooth flow fixes
self crossings but leaves1,784 body crossings; fit03 envelope leaves1,743.
These are failed controls. Body geometry remains complete in each check.

Cavity08 removes exactly1,456 admitted original mask faces plus isolated triangle
5167, retains14,543 source faces, one71-edge boundary and genus1. Cavity09 locates
the handle near the cuff. Parent played41/42 cannot distinguish legitimate detail
from obstruction; no further cut is authorized by that evidence. Cavity11's25
zero-radius paths (17 positive margins,8 distal hits) establish finite distances,
not calibrated hand-volume enclosure. Source08 remains a diagnostic reference.

**Production change:** after exact wearer-hand ancestry is checked, construct a
new complete inner/outer hand glove derivative with actual cuff rim, palm,
dorsum, thenar/hypothenar and all interdigital webs. Follow all15 native segment
fields per hand, with joint rings and continuous field blends. Use existing
hand anatomy as fitting geometry, calibrated clearance/thickness and bounded
web curvature; a normal-offset copy alone can self-intersect and is not accepted.
Preserve donor exterior padded silhouette through explicit semantic chart/bake
correspondence. Mirror a validated R construction with reversed winding and named
R→L remapping, then validate both complete actual hands. Do not select arbitrary
bone-X radial rolls or resume failed RBF/nearest32 envelopes.

Prepared `glove-enclosure12` should be the last prerequisite inventory, amended
before execution to preserve exact source triangle→loop and clipped corner UV
ancestry. The current draft does not do that; a geometric cuff-loop pass is not
UV/chart acceptance. Inventory52 may proceed after committed contacts51 when
parent confirms unchanged body07 hands. It must lead straight into one authored
glove, not another source-hole campaign. Report unsupported seam/topology cases
concretely, preserve arrays and resolve that construction decision once.

## Jeans and boots: deliberate new derived topology is required

Jeans prepared source is still unrigged. Its coarse scale uses boxer waist and
ankle+45mm, but source straight legs differ from target spread. Existing prototype
is not a fit. Author separate legs, true waist/ankle openings and crotch gusset,
with hip/knee loops fitted around the completed body/underwear. Embed source
appearance using semantic front/back/left/right panels; preserve fly/pockets and
seam detail. Waist fields follow pelvis, knee transition follows the corresponding
thigh/shin, and waist/hoodie + ankle/boot overlap is measured under motion. Existing
886-vertex old jeans and local-normal fitting are rejected historical controls.

New selected boots are appearance sources, not the old appearance08/09 boots.
Old08 fails under toe flex: edges0.196–0.214m span abrupt foot/ball L1≈2 changes.
Old09 is a useful moving enclosure control with769 samples, but435/1174 raw
memberships are nonunit (maximum sum1.987204) and shape remains unaccepted.
Dorsal10 lowering loses enclosure and reaches421 upper/body contacts. Reuse the
principle of measured complete plantar surface/sole support, not those skins or
rejected dorsal geometry. Construct selected-source compact boots with sole,
heel, toe box, true ankle opening, ankle/ball loop transitions and source-material
panels. Verify finite sole/peg surfaces and actual skinned support on both bikes;
a rigid marker or centerline is insufficient. Pair mirroring does not by itself
prove inside/outside anatomy or unilateral deformation.

## Preservation and one-wearer execution consequence

Current master is body07 native49, not an earlier body07 draft or hoodie26 body.
Do not fit around shoulder/hip defects simply because a local-source orbit passed.
Contacts51 and held-out played body07 review are first. Head source identity,
protected face/scalp/ears/cheek, inherited UV/PBR, raw packed and decoded normals,
51-joint hierarchy/rest/bind and frame must remain exact. F0's lower-head7,828
editable aliases do not expand the protected face or revive old1,243/464 scopes.
Clothing fixes must not delete head/body triangles or rebind to hide collisions.

Keep one assembled master in the sole native author's ownership. Incorporate each
coherent garment unit into that master after save/reopen/contact checks and commit
its unaccepted checkpoint immediately. Deliver a whole gray/PBR wearer stress
movie as soon as all four garments exist; do not spend the next session making
isolated source galleries. Parent judges forward/reverse neutral/A/T/reach/crouch,
bike leans, grip/release, exposed interfaces and consistent appearance. Full/four
surface loss, all body/head/self/inter-garment targets, export/consumed normal/skin
agreement, physical phone cost and device/stranger acceptance remain mandatory.
