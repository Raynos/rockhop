# Diagnostic authored-key clip08: source handoff

This append-only recipe makes the actual failed corrective06 visible at the
saved author04 key in the real Garage. It does not qualify the shape, contacts,
generic motion or human art. Construction and played Garage review remain
parent-run; this builder has not emitted a GLB, built the game or opened a browser.

The six-second `DiagnosticRestKey` animation contains all 75 original joints and
225 local TRS channels. Its samples are source rest at 0/1 seconds, the exact saved
author04 pose at 2/4 seconds, and source rest at 5/6 seconds. Rotation interpolation
uses glTF LINEAR quaternion interpolation. No morph-weight channels are authored;
the existing generic pose-local corrective helper must evaluate the animated pose.

Parent invocation from repository root, under the existing CPU2/memory guard:

```sh
node assets/blender/rider-rebuild/selected-seated-diagnostic08/append-clip.mjs \
  --out=harness/out/rider-rebuild/selected-seated-diagnostic08/clip01
```

Outputs are ignored `rider.glb`, `rider-contract.json` and `diagnostic.json`.
The contract clones the **constructed02 contract**, retaining measured calibration,
the exact `corrective` activation object and `qualificationState:
FAILED_CORRECTIVE_GATES`. Only the new `glbSHA256`, `previewClip` and
`diagnosticMotion` are added or updated. Diagnostic motion includes full original
authoring and corrective receipts, pins, all 75 identities and endpoint residuals.

The recipe streams input hashes and original BIN copying; it never loads the
359 MB GLB into one buffer. Every original BIN byte is retained and checked against
the corresponding emitted prefix. New time/TRS accessors and animation channels
are appended. Existing nodes, skins, materials, meshes, morph targets, accessors,
buffer views and other source JSON fields remain exact. Source rig order and all
75 names/parents are compared with actual engine05 GLB skin/node order and the
engine05 native contract; all 75 inverse-bind matrices compare byte-for-byte.
Source rest node TRS are preserved; animation samples record float32 rounding.

Immutable inputs include corrective GLB
`2e1b46948be713ede443bc9f159301f876c09aadc331ac25bf477c0d5124cf1a`,
author04 rookie `9d59ba63e99c8d017e7f8c8c4dfbfde0859aafd3ea6d2383c734dec259ec5f8a`,
constructed02 contract `94a2d4b3e6449bc914f22082eeaac247bca1420002af6261faebc76e81fd9c88`
and engine05 contract `2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728`.
The source pins also require the full corrective receipt and engine05 GLB.

Parent integration uses the ignored output asset and contract with the existing
build caller's `--allow-failed-diagnostic`, without `--comparison`. The parent
owns conditional activation and build metadata. Existing Garage review selects
the real clip explicitly:

```sh
node harness/rider-rebuild/garage-review.mjs \
  --build=ACTUAL_DIAGNOSTIC_BUILD --out=FRESH_IGNORED_CAPTURE \
  --contract=harness/out/rider-rebuild/selected-seated-diagnostic08/clip01/rider-contract.json \
  --clip=DiagnosticRestKey --bike=rookie
```

The saved authoring pose came from rookie; that provenance is retained. The clip
itself has no bike selector, camera edits, runtime pose injection or geometry edits.
Default private rider source and production assets are unchanged.

Lightweight validation: two in-memory fixture tests pass for append preservation,
the full TRS schedule, native order, duplicate rejection and identity/parent drift.
Header/JSON-only inspection of the actual input gives pose-local weights 0 at
source rest and 0.9999999999999957 at the float32 saved key, with maximum key hip
angular residual 4.2146848510894035e-8 radians. This is algebraic source inspection;
actual emitted binary preservation, Garage helper activation and moving evidence
remain parent-run gates. Both original failed classifications remain unchanged.
