# Original action transport to a corrected target (source only)

This wrapper has not appended or reviewed a target. The two original actions,
rig export and original engine05 lineage remain pinned through the unchanged
`selected-garage-actions01/input.json`; its config is reconstructed against the
original export receipt before reuse. No Blender process or dense re-export runs.

Copy `input.template.json` to a new config in this directory. Set only
`futureTarget.ready` to `true` and fill its three NEW path/SHA256 pins for the
corrected cuff/hoodie GLB, matching contract and matching calibration. Keep
`accepted: false`. The target contract must retain the original `nativeRest`;
its GLB and calibration source hashes must identify the new target. Original
action provenance is immutable and separate from these new target pins.

Run from the repository root (Python with NumPy):

```sh
python3 assets/blender/rider-rebuild/selected-action-transport02/transport.py assets/blender/rider-rebuild/selected-action-transport02/input.template.json --check-original
python3 assets/blender/rider-rebuild/selected-action-transport02/transport.py assets/blender/rider-rebuild/selected-action-transport02/input.corrected01.json harness/out/rider-rebuild/selected-action-transport02/append01
```

The first command checks only small original provenance and writes nothing.
The second requires a fresh output child and all target pins. The unchanged
append helper checks all 75 named inverse binds exactly, names/hierarchy,
serialized local rest (residual < 2e-6), and every original native action matrix
(residual < 2e-5). It preserves the target's BIN bytes and JSON/accessor/view
prefixes, then writes `rider.glb`, derived contract/calibration and `export.json`.
`transport.json` records original provenance separately from the new target.
Actual Garage playback, moving art, contacts and devices remain for parent
review; these sources grant no normal-player asset promotion or acceptance.
