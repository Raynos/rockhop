# Local authored corrective01 — UNACCEPTED CHECKPOINT

Local pose-space volume preserves the clean original native patterns, basis
rest silhouette, UV, topology and weights. Only117left-underarm and55left-knee
source vertices receive morph deltas. Fixed support is3full native graph rings
plus2smoothfade rings around exact Agent3 source triangles. This is a small
prototype, not a whole-garment solve or normal-player integration.

Sleeve12mm and knee14mm authored posed volume follows local body-nearest
normal plus local intrusion and transfers through exact inverse-ownLBS into
three sleeve keys112/144/240 and one knee key240. Maximum posed correction
12.047/15.614mm and native morph24.822/23.005mm are below fixed40mm posed cap.
The body/rig does not change; complete signed clearance is not inferred.

Controller centers are rest0 plus each authored pose. Distance is square-root
sum of squared native local quaternion angles (acos(abs dot), clamp1), then
normalized inverse-distance^4 weights; distance<1e-5 selects a cardinal center.
Rest zero coefficient is discarded and is exactly zero at frame0. The explicit
controller, centers and529frame coefficients are pinned in streams/expanded-driver.json
SHA `ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457`.
GLB morphs alone do not automate rig-angle coupling in the player.

Target centroid local-normal dots improve: rear-underarm112−2.119→+7.652mm;
front-underarm144−1.621→+9.396mm; knee240−3.912→+8.690mm. Remaininglocal contacts
are12/8/31shirt at112/144/240 and123jeans240. Held-out72shirt contacts regress
121→126, so isolated rays do not certify the prototype. Right/outside regions
retain original defects. Global fit and all M0–M5 remain open.

Validation: original native basis data signatures preserved. ActualGLTFLoader
529samples matches native-four corrected streams within.000442504mmshirt and
.000224423mmjeans; controller error7.77e-16 and jointworld error1.11e-15. Body
all attributes/indices and all51joint orders/hierarchy/binds unchanged. Garment
base positions/UV/sourceIDs/weights/indices are byte identical. **Exception:**
shirt base normal recalculates one vector/3components, max9.99784e-5, explicitly
recorded. Morph support/deltas independently source-mapped; no stale IDs.
Native full/four garment loss4.820/.948mm remains separate. Python/Node syntax
and scoped oxlint pass. Manual matrix assignment marks/forces updates after
the initial verifier caught stale Three world matrices; no candidate changed.

Ignored local GLB SHA `4092f9aa62c01598888712e7cb879439d9bc8093a82effb2b60a9ec1be85193e`;
master/controller pins and full/four streams are in the tracked driver/report.
The source recipes regenerate them. Source prototype/evidence frozen before
matched continuous native and actualGarage review; Agent3 has exact pins.
Root alone judges; no appearance/bodydonor substitution or player promotion.
