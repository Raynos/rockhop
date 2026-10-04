# Read-only grip diagnosis — unaccepted

The old source37 engine control holds open hands on a centroid marker.
It does not author an enclosing finger grip or align the wrist to an actual
finite grip surface. Current native26/29 retain the same rest hand/glove
geometry and absent distal glove memberships; they have no matching actual-bike
played contact certificate. Parent alone judges; M0–M5 remain open.

## Provenance and frames

Preparation commit `a3f3f4c1ca56e6b2a8f7eeb65909c2278bf9d968` pins66inputs.
The human feedback message is `01a10741-9f0b-7552-91b3-4fc7c7c00a04`;
no specific clip was identified. Parent recently showed native source26 film93.
Older wide film50 is therefore a diagnostic control, not proof of which pixels
prompted this feedback. Its recorded silent playback decoded all926frames.
Existing frames0119/0176 were inspected for context; stills are not acceptance.

Source37 SHA `3ffd591d6872513646cab2384f8fe6b21f828ab57bdb5842cc1659fcd32face2`
contains source09 gloves/body,51own semantic bind joints, four JSON-only
markers and no animation clips. The glove has4021vertices. The marker comes
from a source05 body-palm patch centroid and inherits hand rest orientation;
it is not fitted to the source09 outer glove. Native26/29 immutable glove,
rest51bone/parent/head/tail fields are exact to one another. Source37 versus
native26 positions agree within5.96e-8m, bind transforms within1.52e-7;
memberships differ by up to9.3821e-5, so byte identity is not claimed.

Native coordinates: +Xforward/+Zup/−Yleft. File: +Xforward/+Yup/+Zleft.
The axis conversion is `C=[[1,0,0],[0,0,1],[0,-1,0]]`; rig rootX+.65
is applied once. Source glTF positions are baked file world. Effective skin
`K=boneWorld*inverseBind`; numeric47 boneWorld=`K*inverse(inverseBind)`.
Native99 object-local skin matrices multiply native bone rest on the right.
Semantic identities are dotted hand.L/R and index/middle/pinky/ring/thumb
_01/_02/_03.L/R; no nearest-bone reassignment was performed.

Actual bikes are production rookie/pro and their LODs, matched to existing
fit receipt SHAs. Production GLTFLoader+Meshopt CPU decoder reads actual
finite grip triangles through original node22/mesh8/primitive0 identities;
source triangle ordinals remain attached. Source frame originX=.649999976
is subtracted once to get runtime bike.frame coordinates. Detailed grips each
have44triangles, LOD grips16. Closest-point queries enumerate every triangle
interior and every finite edge. Inside tests use full signed solid angle.
No cylinder proxy is substituted for measured contact distance.

## Established defects

The engine targets `[.27,.78,±.33]` and compares marker position plus
rest-oriented wrist rotation. That point is inside every actual finite grip:
rookie/pro detailed L11.350mm/R11.298mm from the nearest outer triangle;
LOD L10.518mm/R10.612mm. These are exact source-point geometry results,
not proof of a physically seated palm. The controller check cannot distinguish
point alignment from skin contact or finger wrapping.

All30finger joints stay at their rest parent-relative transforms over both
176moving film50 streams (OFF/ON) and the separate703pose numeric47 stream;
maximum element residual2.467e-7. Native99's1232archived witnesses also keep
finger locals at rest within8.345e-7. The four non-thumb fingers have only
2.43–11.44deg adjacent segment bends at rest; thumbs20.12–22.90deg. This
establishes absent finger articulation in those fixtures, not a universal
claim about unseen motion.

Because film50 stores no independent bike.frame matrices, moving contact
reconstruction uses an explicitly rider-implied chassis: handWorld rotation
against own rest, translation from worldSocket−R*commandedGrip. Left/right
implied transforms agree within1.154e-6matrix units. That is internal
consistency, not an independent recorded chassis certificate.
Within that conditional frame, detailed rookie distal semantic glove
centroids are Lmiddle81.229mm/Lring79.709mm and Rindex86.261mm/
Rmiddle78.869mm/Rthumb39.048mm from the finite surface. All are outside
through all176samples and stationary to numerical roundoff. Skeletal
terminal tails lie55.4–117.8mm away, but tails are not outer-skin witnesses.
Nearest source glove points to the body-derived markers are3.381mm(L)
and11.830mm(R) away; translating those rest points to the commanded marker
places them12.777mm(L)/7.772mm(R) inside the grip. These are point witnesses
under the same conditional frame, not full palm pressure/collision coverage.

Visible glove binding has no positive distal memberships for Lindex,
Lpinky, Lthumb, Rpinky or Rring. Those absences occur in both native26/29
and source37. Lring distal has only6positive rows. Rthumb differs120native
versus119export positive rows. Semantic memberships do not establish complete
geometric finger segmentation. Curling every distal bone cannot directly
move the missing distal glove regions, so a pose-only repair is insufficient.

Wrist alignment varies while hand orientation remains held at rest:
forearm/hand local+Y-axis angle is7.423–42.224deg in film50, witnesses
ticks248/524; numeric47 separately4.778–42.236deg, ticks247/524.
This is a bone-axis alignment proxy, not an anatomical injury or complete
wrist deviation/twist measurement. No universal target angle is inferred.

## One recommendation for Agent1

Construct one native hand-on-actual-grip prerequisite once root authorizes
that source work: register the outer palm and wrist frame to actual finite
grip geometry, curl fingers/thumb around that surface, and validate semantic
body/glove influence coverage per finger. Preserve own51bind and the admitted
source scope; the missing glove memberships need explicit root authorization
if weight changes fall outside that scope. Do not treat the source05 centroid
or `handOnGrip` debug flag as a seating/wrapping gate.

Then independently record actual bike.frame, all hand/finger bone transforms,
actual palm/finger surface correspondences and finite-triangle residuals
through the already required riding/lean/landing/restart motion. Root must
judge a matching played close view and stranger/device evidence. This report
contains no new source, candidate, solve, weight/pose edit, render/capture,
Library delivery, upload, promotion or admission. Exact future pose angles,
surface target points and influence assignment remain untested design choices.

`measurements.json`, `rest-finger-angles.json`, `native-read.json`, finite
triangles and pinned recipes carry every number and witness. Numeric47 is
never synchronized to film50 pixels. Native film93 is native FK without actual
bike support; absent native contact coverage remains explicit.
