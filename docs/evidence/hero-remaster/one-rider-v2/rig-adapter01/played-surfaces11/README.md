# Body11 actual moving hand and sole surface probe

**Current evidence is `framed04/`.** The original capture lost contacts from
the frame. `framed02` corrected its projection but exposed stale world focus
sampling before the camera presentation. `framed03` stopped at sample zero
when an assertion rejected that sampling order. Their reports and original
films remain historical diagnostics, with preserved private archives; they
are not visible-contact passes or current whole-triangle certificates.

The current probe collects metric vertices **after the final camera render**.
Every one of its 480 final actual surface midpoints projects to the screen
centre, maximum NDC error 1.04e-15. Re-reading after projection gives exactly
zero final surface midpoint drift. The capture source is snapshotted and
hashed in `framed04/process.json`. This is an explicit private projection
window only; no player camera or pose changed.

Literal exported GLB index triangles now define the whole-hand audit.
Coincident UV/normal vertex aliases require exact JOINTS/WEIGHTS/morph
correspondence before using the measured native vertex point. The initial
native-triangle report is separately retained and marked unproven/rejected;
the corrected numerical bound is approximately unchanged. Current film
and metric work below refers to `framed04/` unless explicitly historical.

Builder evidence, unaccepted. Parent must play and judge the clips. Nothing
modifies geometry, rig, physics, materials, player assets or the current face.

The private body11 build consumed SHA
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
Same recorded 40-second input, 480 samples at 12 fps. Every physics state,
state hash and rider debug object exactly matches body09 played01. Maximum
lean reaches both -1 and +1. Events separate all wheel contact transitions
(which include jitter) from at least two sampled frames with both wheels
airborne, and record twelve recovery samples after each landing.

`source-roi.json` matches all 1668 native glove vertices per side to actual
exported body11 positions within 0.119 micrometres. Hand morphs and skinning
are measured via Three.js `getVertexPosition`, then transformed through the
actual world matrices into the live bike handlebar/peg mesh frames. The
unchanged grips use the recovered literal 44 triangles per side. Peg sides
use their actual decoded triangles. Sole regions are the lowest 2.1 mm source
vertices: 56/58 vertices and 67/77 complete triangles.

`report.json` records actual per-sample geometry metrics, state and cameras.
Private float32 point buffers retain all measured points; their hashes are
in `surface-audit.json`. Original native skin weights and measured palmar
axes define the same pad selections used by native-grip03. This CPU pad
analysis was added after capture and uses the retained actual points; it
does not require another rendered run or alter the character.

The actual thumb palmar pads remain **4.785–4.854 mm from the rubber grip**.
Whole-finger minima of a few micrometres occur on other thumb surfaces and
must not be substituted for a thumb-pad pass. Other selected finger pads
have minimum vertex-to-triangle gaps approximately 0.024–0.154 mm.

Whole glove triangle convex-envelope penetration upper bounds across the
480 actual samples are 0.595 mm right and 0.799 mm left. These use linear
programming over entire glove triangles at the first actual sample, then
add the maximum measured bike-local vertex drift plus a float32 allowance.
Quantized grip face planes require up to 1.981 mm inflation to contain all
actual grip vertices, so these are conservative bounds, not exact collision
depth or zero-intersection certificates.

Closest actual lowest-sole vertex gaps are 0.176–0.177 mm left and
0.611–0.612 mm right. Nearest-face sign suggests approximately 0.177 mm left
penetration; that local normal diagnostic does not certify a complete outsole
or peg collision volume. Sole patch drift is at most 1.36 micrometres.

`hands/played.mp4` and `feet/played.mp4` are actual 40-second films, each
alternating camera view at 6 fps. `events.json` identifies 2.4-second films
for each view at maximum forward/backward lean and landing/recovery.
All 240 frames per view are indexed in ten `decoded-*.jpg` sheets each.
Lossless source frames and point buffers are archived under
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/played-surfaces11`.
Far-side contacts can be occluded; metrics and retained surface samples
do not replace played visual judgment.

The current `lockf -k /Users/raynos/projects/localai/.model.lock` render workload
took 54.55 seconds with peak anonymous memory 40.927 GB decimal, below 70 GB.
The initial diagnostic took 54.5 seconds / 41.685 GB; separate bounded
follow-ups are recorded in their own `process.json`, including the stopped
sample-zero assertion. No lock was stolen or another job evicted.
Headless WebKit, silent audio policy, no browser errors. Probe lint and the
complete harness typecheck pass. CPU correspondence, pad/envelope analysis,
archive and event trimming use existing installed runtimes only.

Reproduce: run `prepare.py` with installed UniMate Python, `run.py` under
the shared lock in a fresh evidence directory, `audit.py` with UniMate
Python, `archive.py` with the existing primary Pillow runtime, then
`extract_events.py`. The capture refuses an existing point buffer/frames.
Preserved snapshots are never overwritten by the capture.

Parent round107: reviewed all480 ordered actual frames on20 film pages.
Retain framed04 as diagnostic evidence, with far-side occlusions and the
4.785/4.854mm thumb-pad gaps explicit. Contact quality gate remains open.
Dark irregular elbow sleeve patches require matched gray inspection.
