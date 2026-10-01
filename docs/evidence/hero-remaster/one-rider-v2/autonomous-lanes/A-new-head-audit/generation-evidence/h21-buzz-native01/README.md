# Fresh Hunyuan3D 2.1 buzz source — appearance unaccepted

The parent queued the exact approved buzz reference under the canonical model
lock after commit aa2d5a6b. The real job finished exit zero in 138.002 seconds.
Shape sampling took 26.09 seconds; CPU-rendered/baked 2.1 PBR paint took 88.104
seconds. Actual native shape retained **985,183 triangles before every cleanup
and FaceReducer**; the painted inspection export contains 99,999 triangles.
The source is genuinely new actual 2.1 generation, not a 2.0 substitute, old
curly-head repair or native-palette replacement. The full worker receipt and
unchanged source hashes are in `model-source-freeze.json`.

The first CPU render attempt stopped before any PNG because it required Blender
imported triangle count to equal native triangle count. That assertion exposed an
importer validation difference, not a generation/resource failure or an artistic
score. Exact readonly forensic evidence proves:

- Raw NPZ and raw GLB index payloads contain all **985,183** triangle indices,
  byte-identically after decoding.
- Blender import contains **985,175** triangles. Exactly **eight** source
  triangles were excluded, each with repeated vertex indices and exactly zero
  geometric area. No other source triangle occurrence is missing.
- Original raw GLB vertex coordinates matched the original NPZ after the normal
  glTF-to-Blender frame conversion within 2 micrometers. Source bytes are intact.

`raw-index-forensic.json` retains exact missing face IDs, full index hashes,
duplicate/zero-area counts and actual importer counts. Its CPU-only forensic job
exited zero. `cpu-render-failure01.json`, the exact failed recipe, process report
and log retain the stopped render finding; no guard was silently widened and no
claim that all 985,183 source triangles were rendered is made.

The parent will checkpoint this source-preservation finding before the next
render correction. That correction should show the actual painted face first,
then explicitly label Blender's eight zero-area validation exclusions when
showing raw geometry. Source NPZ/GLB bytes remain the preservation authority.
Nine matched angles, front/profile/three-quarter/rear closeups, gray diagnostics
and the parent's independent 7/10 face judgment remain pending. No bust assembly,
skin/clothing join, rig, weights, animation, contact, runtime or game-ready claim
is accepted. Existing comparison and historical controls remain untouched.

All agent work after generation was read-only CPU, two threads, isolated Blender
state. The parent owns the completed GPU job and released its lock without
eviction. Initial CPU render failed 02:23:03 UTC; raw index forensic completed
02:26:00 UTC. Source/evidence hashes are frozen in `checkpoint-source01.json`.
