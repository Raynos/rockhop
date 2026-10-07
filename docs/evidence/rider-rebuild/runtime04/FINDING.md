# Selected rider engine intake requires the actual outfit

This is an **unaccepted source-only checkpoint**, not an engine build, new
asset export, played visual judgment or completion claim. The final complete
selected rider is still absent. No normal player source or model was edited.

The previous combined04 appearance is rejected. Its measured 75-joint rest,
native anatomical endpoints and socket frames remain an explicit rig control
reference. The new intake cannot admit that reference outfit: it requires
exactly the actual joined head/body, selected hoodie, selected jeans, two
selected gloves and two selected boots. Every material primitive must remain
indexed, visible-capable, skinned and declared under its actual author object.
Actual visibility and parent art judgment remain the played Garage gate.

The JavaScript gate independently decodes all GLB binary accessors. It joins
split material vertices by their current `_NATIVE_ID`, recomputes the named
FOUR fields and compares their hashes with the independent native and decoded
receipts. Canonical positive fields must exceed the installed exporter cutoff,
occupy the exact 2^-24 dyadic grid and retain the existing 2e-7 sum guard. The
joined body's original source IDs and float32 positions are reconstructed in
current native-ID order and checked against their native byte receipts.
Original selected embedded PBR image bytes and primitive inventories are
checked against the decoded receipt. The native receipt must still identify
the actual .blend file bytes.

Only after these checks does calibration transfer become possible. All 75
named joint transforms, full ancestor chains and inverse binds must match
the frozen actual rig exactly. Native rest endpoints, palm/sole socket frames,
explicit hand/finger semantic mappings, source driver axes, limits and
asset-to-bike placement must also match exactly. Even a 0.1 micrometre rest or
sole edit fails this preservation route and requires explicit recalibration.
Changed face and garment geometry is intentional and is not required to match
the rejected coarse appearance. The mass model still uses unchanged joint
centres and native bone endpoints; it does not integrate new clothing mass.

The successful route writes a new calibration with the **actual new GLB SHA**,
the original calibration SHA and the new measured intake-receipt SHA. It never
overwrites the original calibration or substitutes its source hash silently.
The copied adaptive 20-degree parameters still describe socket-centre control,
not finite glove/bar contact or good-looking new garment deformation.

Validation: 12 source regression tests passed, zero skipped, using the actual
ignored combined04 rig reference. Tests cover exact preserved inputs; rejection
of displaced rest joints, inverse binds, sole endpoints, digit mappings and
axes; rejection of the actual coarse outfit; forged source identities; and
cross-language native named-field receipt encoding. The complete selected
intake has **not run** because its final authored asset is unfinished.

The runtime keeps the existing 1024-pixel albedo/512-pixel data-map derivative
policy and the unchanged **96 MiB whole-scene texture budget**. Original source
maps remain embedded and intact. Outfit/LOD aliases must share one parsed
document. This receipt does not measure actual GPU allocation, browser decode
memory or physical-phone performance. No heavy native, build or browser job
ran for this source checkpoint.

Run after the complete selected native and decoded receipts exist:

```sh
node harness/rider-rebuild/selected-engine-gate.mjs \
  --source=COMPLETE_SELECTED_DIRECTORY/rider.glb \
  --contract=COMPLETE_SELECTED_DIRECTORY/rider-contract.json \
  --native-receipt=INDEPENDENT_SELECTED_NATIVE_RECEIPT.json \
  --decoded-receipt=INDEPENDENT_SELECTED_GLB_RECEIPT.json \
  --out=harness/out/rider-rebuild/FRESH_SELECTED_ENGINE_INTAKE
```

Use the generated `selected-adaptive20-pose.json` in the guarded private build.
Run actual-source driver tests with the repository TypeScript loader:

```sh
RIDER_REBUILD_SOURCE=COMPLETE_SELECTED_DIRECTORY/rider.glb \
RIDER_REBUILD_CONTRACT=COMPLETE_SELECTED_DIRECTORY/rider-contract.json \
RIDER_REBUILD_POSE_CALIBRATION=FRESH_SELECTED_ENGINE_INTAKE/selected-adaptive20-pose.json \
node --import tsx --test harness/rider-rebuild/private-rider.test.mjs
```

The parent must judge full natural-speed actual Garage and ride clips, and
run the cold-boot, clear, crash/restart gate on the resulting private build.
Source identity and socket-centre math do not pass the rider art gate.
