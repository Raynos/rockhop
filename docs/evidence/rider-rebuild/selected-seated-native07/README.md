# Native seated corrective07: source handoff, unaccepted

This recipe imports the actual corrective06 deltas into the pinned engine05
native master. It is source-only: Blender import, saved reopening, static export
and moving-art review have **not** been run by this builder.

The input is the failed diagnostic `constructed02`, not an accepted shape.
Its classification and all five geometry checks remain in both native receipts.
There are 7,005 explicit jeans delta IDs and 55 body delta IDs; the corrective
receipt reports unchanged arms. Native import cannot promote those failed gates.

## Parent execution

Run these commands from the repository root through the parent's existing CPU2
and memory guard. Each output must be fresh. No trust preferences need changing.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-native07/import-native.py -- \
  --shape-key=harness/out/rider-rebuild/selected-seated-corrective06/constructed02/shape-key.json \
  --shape-sha256=972bfc0d475fb5641ecfc706fc973d36d5354e64cc5dea3e832d1aac01627917 \
  --corrective-receipt=harness/out/rider-rebuild/selected-seated-corrective06/constructed02/corrective.json \
  --corrective-sha256=a9b78bd1e5b038db5d196149da71e027a84e77134928e961148a098d8abfdf52 \
  --allow-failed-diagnostic \
  --out=harness/out/rider-rebuild/selected-seated-native07/import01

/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-native07/reopen-probe.py -- \
  --receipt=harness/out/rider-rebuild/selected-seated-native07/import01/native-import.json \
  --out=harness/out/rider-rebuild/selected-seated-native07/reopen01
```

An optional separate reopening with `--export-probe` and a fresh output directory
exports and decodes a static morph GLB. It is a transport probe, not the engine
delivery asset. Native outputs remain ignored under `harness/out/`.

## Protected data and driver basis

The recipe streams SHA-256 checks of the engine05 native master
`95a4f14e06fb52cc055df6d1446a035d8cd3d35180d565ad52f3a70b3b05664b`,
contract `2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728`
and source GLB `72b90e8790f8490743a75f8b70791aa21edfee6234cec609093e9b62e08d4bfd`.
It reuses the pinned engine exporter fingerprint, relaxing only its no-shape-key
eligibility assertion. Exact base positions, topology, UVs, corner normals,
materials, packed images, Four weights, object transforms, all 75 rest bones and
the hidden anatomy reference must remain equal before and after import.

Engine05 assigns `_NATIVE_ID` after the equipped-body mask. IDs address that
current native inventory; they are not pre-mask donor indices. The importer
requires the exact current ID sequence, unique finite deltas and the explicit
Blender/glTF delta swizzle. It records float32 target assignment residuals.
An empty masked-body delta list is valid; jeans must have actual deltas.

The installed Blender 5.2 exporter gives joint world rotation `C * Mbone`.
Shared axis conversion and placement cancel in pelvis-relative thigh rotation.
The importer therefore compares native relative rest quaternions directly with
the JSON, with a hard 1e-5-radian gate rather than guessing another axis mapping.

Thirteen built-in drivers use WORLD quaternion components, compute
`inverse(pelvis) * thigh`, then angular distance to `key * restRelative` on each
side. Their combined distance divided by the JSON radius drives the exact
Wendland expression `max(0,1-x)^4 * (4*x+1)`. There are no bike, camera, custom
namespace, embedded Text or script-autoexecution inputs. Each expression is at
most 122 characters for this payload. The native probe requires valid simple
expressions, endpoint/intermediate parity and invariance under common rig
rotation. Saved reopening uses `use_scripts=False` and requires stored rest
weights exactly zero plus the same probes. Those actual Blender gates are pending.

## Export and validation limits

The actual installed exporter warns that `export_apply=True` prevents shape-key
export. The optional native probe sets `export_apply=False`, exports static
targets/default-zero weights and decodes POSITION deltas through `_NATIVE_ID`,
with one 75-joint skin and no extra joint/weight attribute sets. This probe does
not establish full baseline GLB topology/UV/PBR/BIN or decoded Four parity.
Blender's animation driver exporter samples animation effects; it does not
transport this live driver formula. Engine playback must explicitly use the
corrective06 runtime kernel. Corrective06's append-only morph exporter remains
the source-preserving engine route; its failed geometry classification persists.

Lightweight checks completed: all four Python files parse; 150 deterministic
CPU-only expression/kernel comparisons passed, including rest, key, arbitrary
rotations and common placement. The actual constructed02 schema, classifications,
activation and 13-driver graph were inspected. No Blender process was launched.
Contact acceptance, dressed native/engine motion comparison and human art
judgment remain open.
