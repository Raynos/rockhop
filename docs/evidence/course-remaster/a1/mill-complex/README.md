# A1 Sawdust — stair-section mill

2026-09-29, compared in one checkout with the same source except for the A1 mill callsite. **Verdict: retain as an incremental landmark.** An open timber shed, pitched roof, saw carriage/blade, feed conveyor, stock logs and sawdust piles now occupy the empty background behind the stair landing around x218. The rider sees a working-site silhouette while approaching and crossing the stairs. The floor, blade, cladding and roof still need richer material/contact detail; this is not final A1 art approval.

## Played review

The silent [before](before/full/clip.mp4) and [after](after/full/clip.mp4) full Rookie rides at 852×392 both finish at **30.35 s**, zero bails and exact video tail hash `397beb1fcd345e2d`. Both camera reports pass. The [20 fps mill approach and crossing](after/mill-window/clip.mp4) shows the conveyor entering frame, the open blade bay, the stair wheel line and the exit; the landmark sits behind the z±1.5 m riding lane and does not hide a landing. The [contact sheet](after/mill-window/sheet.jpg) is an index; judge the motion clip.

The new model merges into the existing `plaque` scenery batch, without an extra draw call or a collider change. It is gated to `a1-sawdust`. A short [headless SwiftShader inventory](after/perf-a1.json) at 852×392, low tier reports 108 draw calls, 288,565 triangles and 48.3 MiB estimated textures, below the shared static budgets; its slow software-raster timing is not an iPhone performance claim. The full-course ride is exact, but fresh human fault comprehension and physical-device pacing remain open.

This is one step toward the [A1 course brief](../../../../plans/TWELVE_COURSE_REMASTER.md), not a completed course. The gate timing, flume, model materials and complete course arc still require a moving review and uncoached landscape players.
