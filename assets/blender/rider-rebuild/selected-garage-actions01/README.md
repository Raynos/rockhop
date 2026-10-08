# Original native actions on the same selected Garage rider

Status: both original actions transported and played on the same selected rider in actual Garage; sampled75-joint source parity exact. Complete rider qualification remains open.

The input pins engine05's actual selected native/GLB/contract, current contact calibration, and the two already authored native action receipts and candidates. Reach/grip/release uses frames1–145 at24fps (**6 seconds**); crouch/rise/arms-up uses frames1–193 (**8 seconds**). Both original Blender action slots are `OBRiderSkeleton`.

`author.py` library-loads only the canonical rig and the two original actions, verifies exact75 rest and every keyed TRS component/frame/slot, and saves a small editable rig-only `.blend` with both actions retained. It samples the original native world matrices before exporting. Dense meshes, selected maps and garment skinning are never imported or exported by Blender in this operation.

The installed Blender5.2 glTF exporter sources are pinned in the input. `nodes.py` gathers an armature's root joints without requiring a mesh; `tree.py` filters deform bones by `use_deform` (all canonical75 are deform bones). `animation/action.py` includes compatible OBJECT action slots when one animated armature exists. `sampled/armature/keyframes.py` retains every sample when optimization is disabled and armature channel retention is enabled. The recipe checks the installed operator RNA before invoking the pinned flags: ACTIONS mode, one-frame sampling, no key reduction, no frame-range clipping, zero-based exported times, native rest position, unchanged hierarchy, no leaf bones and no armature removal.

`append_actions.py` appends that small animation BIN to the original selected GLB BIN. It remaps channel nodes by unique exact name, checks matching hierarchy and serialized local rest matrices, and compares every decoded integer-frame bone world matrix against the original native samples (`2e-5` maximum residual). It requires all75 translation/rotation/scale channels with145 or193 samples. All original selected BIN bytes—including geometry, images, weights and inverse binds—remain byte-identical. All original JSON node/mesh/image/material/texture/skin values remain identical; original accessor and bufferView arrays retain exact prefixes. The JSON container is reserialized to add animation entries, and the buffer byteLength grows.

The output includes `rider.glb`, a derivative contract and `pose-calibration.json`. Calibration semantics change only in `sourceSHA256`; no contacts, solver settings or art acceptance are inferred from the append. Both named generic clips remain explicitly unaccepted until actual Garage playback.

After the parent checkpoints/reviews this source, run through its existing global lease/CPU2 guard into a fresh output directory:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-garage-actions01/author.py -- \
  assets/blender/rider-rebuild/selected-garage-actions01/input.json \
  harness/out/rider-rebuild/selected-garage-actions01/export01
```

Then use the existing private actual-game builder with that output's source, contract and calibration; choose one of these exact clip names with `--garage-clip`:

- `UnacceptedSelectedDressedReachGripRelease145`
- `UnacceptedSelectedCrouchRiseArmsUp193`

At the original source checkpoint, only Python AST/syntax checks had run. Subsequent actual export, transport and Garage results are recorded below. A mismatch fails explicitly; this source contains no fallback animation, clothing substitution, mask, reweighting or geometry repair.

The first actual guarded run saved the small editable native and exported both rig actions successfully (**0.648 seconds** in the exporter), then failed the append intake because Blender also emitted one legitimate75-joint armature skin. The append source now accepts that rig metadata only after exact named-joint and float32 inverse-bind equality against the original selected skin. It still preserves the original selected skin JSON and its original BIN bytes. MAT4 readback uses a read-only mmap of the source file, avoiding a357MB payload allocation. Hierarchy/rest thresholds and all225 channels per action remain unchanged; duplicate sampler accessors are valid.

Reuse the pinned existing export01 rig/NPZ/receipt with the corrected helper, under the parent's serialized NumPy CPU2 guard; **do not run Blender again**:

```sh
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python \
  assets/blender/rider-rebuild/selected-garage-actions01/append_actions.py \
  assets/blender/rider-rebuild/selected-garage-actions01/input.json \
  harness/out/rider-rebuild/selected-garage-actions01/export01 \
  harness/out/rider-rebuild/selected-garage-actions01/append02
```

The corrected input pins the actual small GLB, native matrices, editable native and original rig-export receipt. Resume reconstructs and verifies the original input hash, allowing only the helper SHA and explicit resume provenance to differ. Original large native/action inputs were already pinned during the successful rig export and are not reloaded or rehashed on resume. The selected source GLB remains freshly SHA-checked before copying. The new export receipt retains the original rig-export receipt, author-recipe SHA and input SHA alongside the corrected helper/config hashes. The existing export01 artifacts remain unchanged. The repair initially received AST/source-pin checks; actual results are recorded below.

Actual append02 succeeded in0.756 seconds. See `docs/evidence/rider-rebuild/selected-garage-actions01/transport02/`: both225-channel actions preserve every original selected geometry/image/skin byte, with maximum decoded native world-matrix residual4.487e-6. Both original clips subsequently played continuously in actual Garage; see `docs/evidence/rider-rebuild/selected-garage-actions01/played01/`. All75 localTRS match the original clip exactly at five actual times each. Cuff details, deep seated/full range, finite contacts, GPU vertex parity, production topology/LOD and physical-device acceptance remain open.
