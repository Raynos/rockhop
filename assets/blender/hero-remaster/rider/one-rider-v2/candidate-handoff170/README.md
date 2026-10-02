# Strict C19 candidate handoff170

`map_candidate.py` is a CPU-only JSON adapter for explicitly supplied
C19-derived construction exports. It changes canonical joint names, adds four
contact sockets and copies current mapped-reference metadata. It preserves
every source BIN byte and all non-node JSON: geometry, normals, UVs, skin,
morphs, materials, embedded images and source animations remain untouched.
Outputs stay private and explicitly unaccepted. No appearance, anatomy,
intersections, gameplay or Garage-blending gate is cleared by this mapper.

Before mapping it requires exact ordered19 rest hierarchy, ancestor/local and
world transforms, skeleton root and inverse-bind content against the supplied
mapped V5 reference. Changed joint anatomy/rest/bind or mesh placement is
rejected pending a new explicit adapter. It does not infer a new skeleton.
Five primitive namespaces are required. Protected primitive1 is glove
mesh0/primitive1; protected primitive3 is main head mesh1/primitive0.

Protected position/normal, all UV/color attributes, joint/weight lanes, morph
content and normalized flags must match exactly. Texture checks resolve
embedded image bytes, sampler values and semantic PBR bindings, allowing
harmless embedding-reference relocation but no donor, image or PBR changes.
Only unsigned triangle-index width may differ when every triangle value is
identical; that lossless encoding difference is reported. Source encoding
itself is never rewritten. Each of the five fixed primitive namespaces must
retain its own resolved PBR binding; an unchanged material collection cannot
hide a garment primitive being rebound to another retained material. Other changed garment geometry remains unjudged.

The supplied mapped reference must carry
`WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS`, sleeve-conditioning bypass and an
unaccepted flag. Contact metadata is copied byte-for-byte from that reference,
not reconstructed from ancestral bind04. New socket local matrices reconstruct
its verified rest-world frames under the compatible C19 hands/feet. Historical
`declaredUniformScale:1.015` stays inert provenance; applied scale is1.0.
A fresh output directory is mandatory, so earlier evidence cannot be replaced.

Run from the repository root, supplying actual source/reference paths and a
fresh private child directory:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py \
  --source /absolute/path/to/C19-derived-candidate.glb \
  --reference /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/physical-v5-control157/rider.glb \
  --output-dir /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/candidate-handoff170/new-candidate01 \
  --fixture /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json
```

Omit `--fixture` only when rest-fixture compatibility is not requested. To
reproduce the controls, use the retained rejected outward diagnostic source,
a new verification directory, and append `--verify-controls
--cpu-fixture-smoke --verification-report /absolute/path/to/verification.json`.
The controls create private corrupted copies, never repair or modify sources.

Frozen verification04 results: positive diagnostic handoff plus lossless image
relocation pass; fifteen negative/reuse controls reject without writing a new
mapped asset. Controls cover per-primitive garment material swaps, rest position/hierarchy, inverse binds, protected
head position, glove UV/weights/normalized color flags/morphs, image bytes,
reference axes/bypass/contact version/name contract and reused output paths.
Reference rest centres differ from the fixture by at most2.78e−17 m. Five
actual stock Three.js CPU protocol frames—neutral, sitting, leaning, left-arm
overhead and right grip—have19 bones/five meshes, finite sampled positions and
maximum world-matrix error1.34e−15. Only fifteen vertices per frame are sampled;
this is export wiring, not a5404-frame or deformation-quality test.

Verification03 remains preserved privately. Verification04 adds a control
that swaps only garment primitive0 to a different existing material; it is
rejected by the per-primitive binding guard without changing the material
collection. The first setup rejection of widened protected indices is retained privately
as outward-diagnostic01. Explicit lossless index handling is tested afterward;
no vertex-attribute guard was relaxed. A shell hook refused an overwrite-style
redirect for the optional private smoke recipe; create-new writing succeeded.
The recipe is now embedded in the mapper for reproducible control runs.

Authoritative reports:
`docs/evidence/hero-remaster/one-rider-v2/candidate-handoff170/verification.json`
and `mapping-report.json`. The tested outward garment remains rejected art;
the diagnostic mapped GLB is not production and must not be promoted.

Limitations: embedded single-buffer, uncompressed accessors only (sparse is
supported); changed rest representation is rejected even if visually similar.
The optional CPU loader omits images in memory. Rest-compatible geometry may
still be anatomically wrong. This does not validate continuous motion,
self-intersections, contact surfaces, rendered textures or player acceptance.
