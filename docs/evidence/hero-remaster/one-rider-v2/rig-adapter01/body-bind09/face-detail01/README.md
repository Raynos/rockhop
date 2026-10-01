# Read-only face detail audit — white body09 retained

Both actual source head maps are1024² and loaded maps remain1024², with sRGB,
linear/mipmap filtering and roughness.62. The loader shrinks clothing2048→1024
and glove data2048→512 but does not shrink the head. Raising its texture cap
cannot restore absent source pixels. Spatial front-face UV diagnostic measures
about1115texels/m; this is density, not an appearance score.

Actual6s PBR/gray72frames each consume source09 exactSHA and produce equal
state/debug values at every tick. Anonymous peak34.128GB,32.339s under canonical
lock. No model, rig, physics or normal player rendering change.

The requested1.3m face camera was clamped by the real orbit minimum3m. These
clips therefore remain half-body material diagnostics, not proper face-closeup
acceptance. Keep this control and use explicit private camera projection zoom
with measured effective camera fields next. The harness correction changes
only review framing. Source shape/textures and shader response stay fixed.

Parent reviewed source atlas and textured/gray frame0; whole decoded clips are
retained in order below. Native gray reveals eye/lip asymmetry and blunt hair
mass; textured view adds coarse cheek/eye detail. No new face score or gate
pass is claimed from inadequate zoom or texture-density numbers.

Recipe: `audit_atlas.py` plus `run_capture.py` in the mirrored asset directory.
Lossless72PNG frames per clip are preserved privately with per-frame hashes.
Checkpoints2/3, Garage/Pro/realLOD/surface contacts remain open. No generation
failure counter increment: this is a read-only cause audit and camera setup
finding, not a failed source repair.
