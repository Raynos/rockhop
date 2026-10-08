# Actual selected hoodie PBR intake — source only

Preparation source is ready; Blender has not run. Parent must checkpoint source,
finish patched-target inspection, then assign the serial CPU2 lease and 180 or
600 second process guard. Parent alone judges the art. All R0–R5 remain open.

```sh
python3 assets/blender/rider-rebuild/production-hoodie02/check_source.py
```

The bounded native preparation command, inside the parent-assigned guard, is:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-hoodie02/prepare_dense.py -- \
  assets/blender/rider-rebuild/production-hoodie02/controls.json \
  harness/out/rider-rebuild/production-hoodie02/prebake01
```

It opens the exact complete-body patched target and imports the actual original
4K dense/PBR sculpture. The original glTF has one identity node, 716,971 position
vertices, and two embedded 4096×4096 PNGs. Blender maps glTF Y-up to `(X,-Z,Y)`;
the frozen dense torso and sleeve controls already use that imported frame.
The historical selected-native +90° frame and current target -90° frame cancel.
The helper verifies imported world bounds against converted raw accessor bounds
before applying the frozen `fit_point(..., dense=True)` function.

The helper saves `fitted-original-dense-pbr.blend` before views or bake, plus
`prepare.json`. It checks original PBR node connections, packed image hashes and
UVs, target geometry/UV/weights/material slots/modifiers, and complete body/75
rig parity. Both original donor and target stay available for parent matched
inspection. No atlas, bake, target edit, export or player promotion occurs.

After parent inspection of the fitted dense sculpture, the existing frozen
`production-hoodie01/repair_axilla.py` bake entry point can produce the first
2048 review derivative using its original inputs and author receipt. Its patched
`__file__` remains the recipe authority; calling base `author.py` directly would
fail the authored recipe pin. Keep its required fresh output under
`harness/out/rider-rebuild/production-hoodie01/`. Original 4K bytes remain frozen.
No cage/ray-distance acceptance or larger-ray campaign is authorized here.
