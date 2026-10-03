# Separate anatomy and garment foundation

2026-10-03 · ask261 · builder session01a1013b-2fce-7613-a549-da881625200e.
**UNACCEPTED structural control. No production selection changed.**

The selected source is the already installed CC0 MakeHuman hm08 anatomical
body, baked as an adult male, fitted with the independently authored native
male_casualsuit02 sweatshirt pattern. The old generated rider supplies identity
and later appearance transfer, not an immutable deforming underarm surface.
The MakeHuman [asset license](https://static.makehumancommunity.org/about/license.html)
and local asset headers identify these core assets as CC0. Installed MPFB code
is GPL; no add-on code is copied into the deliverable.

[Source choice](source-choice.json) pins body, native rig, garment and generated
identity donor. The supplied17078byte architecture ZIP hash matches; the approved
overview and ten-frame ZIP were materialized through the Library helper and
their actual pixels inspected. Legacy tube/cap and pinned-boundary failures were
read before construction. The sweatshirt is a structural control, not a claim
that stock clothing/head match the approved rider.

[Control01 construction](control01/construction.json) freezes a new body and
garment in one frame. Body:13380vertices/13378polygons, one component, zero
boundary/nonmanifold edges. Sweatshirt:1250vertices/1204polygons, one component,
four regular openings: two20vertex cuffs,20vertex neck,36vertex hem. Separate
trousers and opaque boxer coverage each have three regular openings. All source
files remain hash-identical. No fused source surface, foreign bind, corrective,
cap, hidden insert, generated texture mutation or GPU model job is used.

Native source weights are retained with one declared spine collapse and explicit
runtime19role names. The independent full rig retains fingers/toe details. Its
file root is x0.65, making the ordinary runtime wrapper x−0.65 cancel correctly.
The native anatomical left/right labels are explicitly mapped by measured game
coordinates (+Z is game left). glTF uses metres,+Xforward,+Yup. SourceA and C19
inverse binds are never copied.

## Limits and next qualification

Control01's generic FK stress sequence is unaccepted. Requested T/A angle accuracy,
actual exported LBS parity, body/cloth clearance, neutral/forward/bent/raised
multiangle motion and bike endpoints remain measured next steps. The exporter
reported truncating some native vertices to four influences; that warning is
retained, not hidden by a bind pass. No runtime sleeve-conditioning optout is set.

The complete anatomical head in this gray control is a fitting reference.
The61393vertex generated head and its materials remain immutable in body11;
retaining its exact separate geometry and fitting the neck interface are pending.
There is no fitted hood, pouch, cuff thickness, baked fabric detail or9/10score.
The real bike contact/standing-seated trajectory, Garage, gameplay, LOD, iOS and
stranger gates remain open. Parent judges played clips; clean topology is a
construction finding only.

## Played and exported qualification

[Played four-view movie](control01/played-four-view.mp4) contains97frames at12fps
with front/profile/rear/other-profile views of the same animated Blender source.
It is a diagnostic of gray native anatomy and flat-color native garments, not
approved face/hoodie artwork. The generic authored rotations labelled T/neutral
do **not** form those requested poses; do not infer trueT/A acceptance or failure
from those labels. Their literal controls remain frozen rather than rewritten.

[Export manifest](control01/export-manifest.json) measures193Three.js animation
samples,51skin joints, exact original inverse-bind tables, mesh/root/bind matrices
and the19runtime roles. Independent action-off fixtures in that manifest solve
trueT, straight45degreeA and neutral arm directions from this bind. They have
zero morphs/correctives. glTF keys start at1/24s and end at193/24s; sampling adds
that first-key offset to the source-relative time. An initially reported0.65m
rest discrepancy was a verifier coordinate error: raw geometry is in file space,
skinned points in mesh space after bindMatrixInverse. Correct comparison gives
maximum rest error0.854µm. No asset/root correction was needed.

[Four-weight comparison](control01/four-weight-parity.json) quantifies the
exporter's warning. At seven source endpoints, worst source→export error is
7.645mm for body and4.716mm for sweatshirt (raised stress);71body rows and10cloth
rows exceed1mm there. Rest correspondence is under0.937µm. Keep this failure
explicit; a later construction must reduce source weights deliberately and
prove exported parity rather than silently relying on truncation.

[Surface motion](control01/surface-motion.json) measures49source times. It finds
body/garment contact even at native rest and folds in generic rotations. BVH
overlaps and nearest-normal dots are witnesses, not penetration depth or a
global signed inside classifier. They **do not** establish garment clearance.
Requalify true requested endpoint poses before choosing shoulder corrections.

[Reference contract](../../../../assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/control01/references/reference-contract.json)
pins actual action-off A/T/neutral anatomy with separate opaque boxers in both
Y-up and Z-up OBJ forms. OBJ subtracts file-root x0.65 and is centredx0; that
adapter must not be applied twice. [Eight A input views](control01/reference-views/render-contract.json)
are calibrated geometry inputs, not art judgments. The native face is gray
fitting anatomy; keep the separate61393vertex generated head/PBR as identity.

No body proportion acceptance is claimed: shoulder centres are±0.196m at1.459m;
native upper-arm length is about0.265m versus the supplied old-source target
about0.330m. This requires parent comparison before treating the fitting control
as the approved final body. Native length targets can reshape body/helpers and
refit garments coherently; pose-specific scale hacks are not an alternative.

The final local-successor handoff is [HANDOFF.md](HANDOFF.md). Builder writes stop
at the request to migrate active work to a new local task.
