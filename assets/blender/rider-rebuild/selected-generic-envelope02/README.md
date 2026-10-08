# Selected native75 generic envelope

Unaccepted source-only review action, separate from the existing 145-frame reach/grip
film. The parent runs this on a fresh, exact corrected masked export; no engine
number or future artifact hash is assumed.

```sh
blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-generic-envelope02/author.py \
  -- /absolute/config.json \
  /absolute/repo/harness/out/rider-rebuild/selected-generic-envelope02/FRESH
```

Config contains `accepted:false` and `native`, `baseContract`, `sourceReceipt`,
each an exact repository-relative `path` and `sha256`. The source verifies the
actual export receipt, canonical 75-bone rest, seven visible meshes, and hidden full
anatomy reference. It saves one editable 193-frame action at 24 fps: neutral,
12 cm crouch with 4 cm rearward pelvis shift, rise, arms 125 degrees from down with
20 degree elbow bend and 8 degree clavicle contribution, exact neutral return.

Native roles and measured limb lengths drive the two-bone target solves.
Every frame keys all 75 local TRS channels and checks fixed sole frames; nine
stations also evaluate three actual finite boot vertices per side. Those
points are selected from the native foot/toe-only weighted lower sole, rather
than treating an ankle joint as a ground contact. Geometry, UV, materials,
weights, rest matrices, and object visibility remain fingerprint-identical.
The action provides no bike pose, balance simulation, or clipping correction.

Source preparation checks: Python AST passes. Independent NumPy target checks
covered 384 continuous phase samples per side: all reachable, knees remain on
their own side, minimum reach margin 1.27 mm; maximum knee flex 64.24 degrees.
Actual unchanged engine03 boot source provides three unique support points per
side with triangle area 0.00809 m². These checks do not replace a Blender run,
played clothed film, or parent judgment. No Blender/render job was run here.

Authoring temporarily disables only the seven dense meshes in the viewport.
The armature remains visible and evaluated. Both boots are enabled for the
actual station measurements, then suspended again. All scene `hide_viewport`,
per-layer `hide_set`, and `hide_render` values are captured and must restore
exactly before fingerprints/save; the receipt records before/after values.
This optimization has not been timed in Blender.
