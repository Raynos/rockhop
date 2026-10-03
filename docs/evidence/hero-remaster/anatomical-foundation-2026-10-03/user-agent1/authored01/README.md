# Authored skin contract diagnostic — unaccepted

A new own-bind skin must have a deliberate loader contract. This diagnostic
uses the existing nearest-asset declaration on ONE new metadata derivative;
no loader code, global behavior or normal player asset changed.

Original GLB7dd161b3 and derivative2df79a77 share identical complete BIN chunk
SHA780b46c8, geometry, attributes/weights, all51joints, hierarchy and inverse
binds. Only JSON node56 `Foundation file frame, game x0.65` receives
`extras.rockhopRiderSkinConditioned=1`. The immutable original529-frame driver
is reused; no silent driver/hash substitution.

[Exact source/regression report](authored-declaration.json) verifies four meshes
through direct current sleeveSkin and actual GltfRider cloning, repeated
Garage/riding switches. Ten shipped full/LOD geometry signatures remain
identical with the tagged candidate sibling. All26existing scoped-loader/hero
regressions pass. Syntax/scoped lint pass.

Why: native source4weights are explicitly authored on this complete own-bind
rig; legacy Gaussian/elbow conditioning independently changes body28.100mm
and cloth25.604mm under stress. Preserving the declared authored contract
removes that extra transform; it does not repair or conceal native-full→four
loss7.811/4.820mm, kept in the separate full/four movie.

Sixth-round ordinary player gate passes silent Metal cold boot,4810identical
ticks/40.083333333333336s clear, crash103, one-tick restart/3.46ms, no errors;
[report](../ship-round6/report.json). Candidate was not promoted or driven
by normal physics. Agent3 independently validates the metadata and normal
loader against raw authoring/source samples and preserved shipped controls.

Limits: garment contact/self witnesses persist; no clearance, likeness,
wearable fit, bike support, phone or M0–M5 acceptance. Root alone judges
played shape; metadata scope cannot accept construction.
