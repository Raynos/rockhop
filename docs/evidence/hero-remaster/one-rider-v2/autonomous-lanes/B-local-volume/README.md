# Lane B — local garment volume, failed pre-volume trial 01

**Unaccepted, stopped at one failed panel gate.** Actual GLB reimport witnesses show
an open, jagged hood with exposed inner islands. There is no reconstructed garment,
neck attachment, motion approval, rig adaptation or game-ready rider here.

The isolated CPU pipeline first clips a named 40 mm local garment region using a
continuous per-vertex distance field around the preserved source collar. It requires
one degree-two outer cloth contour before constructing an implicit annular garment
volume and extracting its surface with scikit-image marching cubes. The first gate
produced **three contours: 187, 143 and 17 edges**, despite zero nonmanifold edges.
The marching-cubes stage did not execute. This is a real failure, not volumetric
success. The prior six neck failures remain; this distinct approach has one failure.

The failed witness retains 44,016 untouched source triangles with exact original
positions, both UV layers and material indices. The local crossing triangles have
interpolated UVs. Original two material slots and embedded body/glove textures are
retained. The complete NEW native head, neck and clavicles plus eyes are unchanged,
placed uniformly at scale 0.42 and world Z offset 1.59338. The approved native
geometry and African atlas foundation are not an accepted likeness; weak brows
remain. Source Blender files and the preserved H21 selection mask have matching
before/after SHA-256 hashes in `trial01/source-audit.json`.

Replacing a Blender mesh cleared its object vertex-group definitions during witness
export. The corrected exporter recreates the exact 163 source names and unchanged
source-indexed weights. Raw weights are preserved separately. New split-edge weights
are unmeasured, and this failed static witness has no rig/contact claim.

Actual evidence is in `trial01/`: PBR and gray neck front, profile, rear and
three-quarter views; full front/rear and face front/profile. They are rendered from
an independent GLB import with matching cameras, 640 px, Cycles CPU, two threads,
16 samples. `reimport-and-renders.json` records actual image/material/UV metadata.
No bend or turntable was run after the failed geometry gate. Parent must judge the
actual images against the minimum 7/10 full-body and face bar; topology is not an
appearance grade.

`environment.json` and `requirements-pinned.txt` record the new isolated Python 3.10
venv with NumPy, SciPy, scikit-image and trimesh. Its shared underlying interpreter
is `/Users/raynos/.local/share/uv/python/cpython-3.10.19-macos-aarch64-none/bin/python3.10`.
Blender is the shared `/Applications/Blender.app/Contents/MacOS/Blender` binary,
5.2.1 LTS with embedded Python 3.13.13; config, script, extension and temp roots are
isolated. No working ComfyUI/Pixal environment or global packages were changed.
Peak external Python RSS was 105,463,808 bytes; witness Blender export RSS was
687,456,256 bytes. All jobs used CPU with two threads, with no GPU/Metal/model job.

Runtime masters and fields are under
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/`.
`trial01/frozen-manifest.json` records exact recipe/source/GLB/image hashes.
A specific next alternative would use intrinsic garment-surface distance rather
than Euclidean distance across folded layers, then verify one true contour before
any volume extraction. That alternative has not been run; freeze and commit this
finding first. Repeating this same gate with hidden radius tweaks is not permitted.
