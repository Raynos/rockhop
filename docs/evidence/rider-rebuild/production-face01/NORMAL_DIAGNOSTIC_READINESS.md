# Saved selected-normal discrepancy: read-only diagnostic source

Finding: the parent reports the first construction saved native SHA
6c80f6e8acc9b50c1d3cc30c92ca70e65148d84be6315e2100584b6f573953e4.
Its independent readback passed exact original below-cut rows, polygons/UV,
hands and master75 checks, then failed actual corner-normal parity: maximum
vector error 0.01461223852 against the unchanged 2e-6 threshold. The old
builder checks its float layer before assigning actual mesh custom normals.
That check does not prove the saved `Mesh.corner_normals` values.

Cheap raw donor inspection finds 33,299 protected coordinate groups, 6,282
with duplicate raw vertices and 6,211 with different normalized source normals.
The builder's `raw_lookup` welds by coordinates only. Some source seams have
almost opposite normals; others can differ within Blender's split threshold.

Official Blender source describes automatic sharp-edge creation when source
normals differ enough, then averaging remaining custom normals per smooth fan
before encoding them as short2. The encoder and decoder also introduce a
quantization/fallback mechanism. These are concrete hypotheses, not the
measured cause of this saved native yet. The installed glTF importer treats
normals as vertex data while its merge code considers all per-vertex fields;
our construction bypasses that geometry import and welds only positions.

Primary references (main is research context, not the installed build pin):

- [Blender smooth-fan splitting and averaging](https://github.com/blender/blender/blob/main/source/blender/blenkernel/intern/mesh_normals.cc#L1394-L1477).
- [Blender custom-normal short2 encoding](https://github.com/blender/blender/blob/main/source/blender/blenkernel/intern/mesh_normals.cc#L711-L753).
- [Blender 5.1 release implementation](https://github.com/blender/blender/blob/blender-v5.1-release/source/blender/blenkernel/intern/mesh_normals.cc).

The proposed guarded command is:

```sh
blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/production-face01/diagnose_saved_normals.py -- harness/out/rider-rebuild/production-face01/normal-diagnostic01
```

It opens only the pinned native and reads the pinned genuine donor. It records
raw-vs-retained-vs-actual errors and the worst 12 protected corners, all their
incident corners, source normal variants, smooth fans and sharp edge flags.
The single worst vertex gets at most three tiny unlinked scratch references:
same one-ring topology/flags, identical topology with all sharp edges, and
identical triangle coordinates with disconnected corners. Comparing those
readbacks separates fan averaging from single-corner normal-codec loss. All
scratch meshes are removed. The actual Blender version/build hash is recorded.

Validation: diagnostic AST parses and its native/donor SHA256 pins match.
No Blender diagnostic has run. See `normal-diagnostic-source.json` for the
exact recipe hash and command before parent checkpoint and CPU2 lease.

Limits: no candidate rewrite, save, fit, render, tolerance inflation or second
geometry candidate. The saved native and its normal arrays/sharp flags must
remain unchanged. One-ring boundaries can change geometric fan bases; the
report provides the whole actual fan context needed to interpret scratch
results. No corrected-normal or moving-art claim is made.
