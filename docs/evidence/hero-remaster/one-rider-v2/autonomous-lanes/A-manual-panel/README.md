# Lane A: explicit seam-landmark panel

This first geometry trial failed before deleting any collar panel or loading the
new native head. There is no assembled character to score or rig. The parent
judges; all four rider surface contacts and motion gates remain unmeasured.

The method specified eight physical garment landmarks on the immutable corrected
glove/body source. Source-edge geodesic paths connect those landmarks with a
segment-distance cost. It uses neither a radius/ring threshold nor an ellipse.
The recorded 88-edge seam is a simple circuit with degree two and no intersection
with the old 111-edge opening. However, traversing from that opening while
blocking the seam reaches **all 42,505 retained source faces**, including both
sides of all 88 seam edges. It therefore does not isolate a local collar panel.
The protective area guard stopped the recipe. No guard was widened.

See `trial01/failure-board.jpg`, the four actual `failed-seam-*.png` views,
`trial01/seam-guard.json`, `trial01/report.json` and `trial01/forensic.json`.
The red line is an exact diagnostic source-edge overlay. These are an open source
prefix with the historical head removed, not a new rider, material trial or join.
The original `.blend` and exported `.glb` prefix are retained in the ignored
LocalAI runtime `autonomous-lanes/A-manual-panel/trial01/` directory with hashes
in the forensic report. Source body, new head and selection-mask files remain
hash-identical. Actual source face indices reached and seam vertex IDs are kept.

The first setup failed because BMesh index lookup needed `ensure_lookup_table()`
after deletion; its exact recipe and log were committed separately. Corrected
setup passed without changing seam landmarks. The first geometry trial is a
distinct failure. Parent-maintained historical family count is eight: six earlier
neck methods, one setup failure and this geometry trial. No automatic count reset.

Blender 5.2.1 LTS and its Python 3.13.13/native modules are shared installed
binaries, disclosed and hashed in `setup.json`. Lane A uses separate config,
scripts, extensions and temporary directories; factory startup loads no user
add-ons. Blender/Cycles and numerical libraries are limited to two CPU threads.
No GPU workload, downloads, package installation, player/physics/bike changes or
commits were performed by this builder. The separate board composer uses the
shared Unimate Python/Pillow for layout only, with its identity recorded in
`trial01/failure-board.json`; it contributes no geometry dependency.

Started 2026-10-01 01:32:11 UTC; unchanged hard deadline 02:17:00 UTC. Corrected
setup completed 01:38:39 UTC, first panel guard failed 01:45:16 UTC, exact
read-only forensic views completed 01:47:14 UTC. No retry or further geometry
selection occurred after the first panel failure.

The next materially different proposal is a valid modular clothing architecture:
preserve continuous native head/neck/clavicle skin, with its real lower boundary
hidden beneath an independently authored garment collar. This removes the
unnecessary skin-to-cloth weld requirement. It still requires nine-angle and neck
motion evidence, actual hidden-boundary clearance, compatible skin-to-skin seams
if any, and a future explicit common rig/weights mapping. It must not be an
overlapping pair of closed skin shells. This alternative is **not executed** in
this checkpoint. Full-body and face quality remain below the new parent-scored
7/10 minimum because no new full character has been produced in this lane.
