# Native landmarks for the selected white rider

Read-only measurement checkpoint, not a rig or appearance gate. All three owned
Blender runs completed on CPU with two threads, within the fixed 30-minute batch
and an isolated configuration. No protected source was saved or changed.

The selected complete donor-fit05/rider.blend has 22,600 body/hood vertices and
61,129 head vertices, no vertex groups and no armature modifiers. Its 1,668 native
hand vertices on each side correspond to the protected body authoring source at
**0.0 metres maximum position error**, with unique matched vertices. The exact
correspondence and original per-vertex weights are frozen in
native-weight-transfer-map.json; those weights have not yet been applied.

native-bones.json records all 163 actual native bone rest matrices, parents and
heads/tails from the untouched MPFB source. report.json maps the actual native
wrist, MCP and finger chains into the complete authoring frame. The skeletal palm
centre is the midpoint between wrist and the four MCP joints, not a skin contact
point or an invented fingertip socket.

## Visible palm orientation and runtime frame

The four actual neutral PNGs include literal markers: red is the positive source
canonical normal, blue the negative normal, yellow the internal native bones.
Front views show fingernails on the red/dorsal side; rear views show pads and
creases on the blue/palm side. Thus **palm-facing is negative canonical normal**
for both native hands. surface-witness.json records the two actual surface-ray
hits with source triangle vertex IDs. The builder makes no appearance score;
the parent must judge these witnesses independently.

The parent's verified runtime convention is +X forward, +Y up, +Z semantic L.
The proper rotation maps source Blender (X,Y,Z) to runtime (-Y,Z,-X), determinant
+1. It maps source +X/native L to runtime -Z/semantic R and source -X/native R to
runtime +Z/semantic L. cuff-runtime-frames.json explicitly remaps sides and gives
points both in the axle-midpoint frame and with +0.65 X in file/rear-axle-origin
frame. The runtime scene subtracts that offset. Do not use the reflected mapping
(-Y,Z,+X), and do not blindly keep native suffixes on the runtime skeleton.
The rest palm-facing axis becomes mostly -X/backwards while fingers point down;
a riding grip therefore requires actual articulation, not a suffix swap alone.

## Cuff and body envelopes

The source 62/65-edge cut rims, 22-edge transition rims, and 22-edge native wrist
rims also map exactly to the complete mesh. Their bounds, axial and radial
ranges are recorded. Source-cut to native-rim axial centroid separations are
14.254 mm and 14.972 mm. These are **connected physical transition rings**, not
separate overlapping sleeve shells. The hoodie cuff top is a texture transition
on the source garment, not a separately named anatomical boundary; no hidden
overlap or moving clearance is claimed.

body-envelope-sections.json contains actual horizontal triangle-plane surface
intersections, arc-weighted centroids, bounds and closed-loop status. These are
clothing/skin envelopes. Clothing hides shoulder, elbow, hip, knee and ankle
joint centres, so none is labelled measured. The rigidly transported native
proximal bones in surface-witness.json are not valid new-body joints: for
example their transported shoulders land inside the torso near Z 1.19 rather
than the new garment shoulders. Use new documented joint estimates and actual
deformation tests instead of transplanting that complete native skeleton.

The measured bottom-2-mm sole clouds and centroids are surface witnesses, not
chosen peg sockets. Standing-to-sitting, final 19-bone bind/socket adaptation,
visible palm/grip and sole/peg contact, maximum lean and recovery remain untested.
No fixed curl, geometry edit, historical production donor, GPU job, or normal
player asset change was made.
