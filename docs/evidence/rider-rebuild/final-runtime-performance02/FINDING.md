# Private candidate normal-runtime checkpoint

UNACCEPTED. The parent still owns moving review and release judgment. No
normal player pin, production runtime or quality setting changed in this round.

The combined source-preserving candidate renders 789,373 hero triangles
including the Rookie bike on normal C1, versus 2,581,869 in the previous
selected source. Submitted triangles fell from 5,258,462 to 1,673,470 at
median, a 68.18% reduction. Garage draws 1,643,362 at median and explicitly
reports no hero reflection. The original Mustard control still draws 121,984
median on C1 and 282,981 in Garage. The actual renderer used DPR 1.5
with canvas 1266×585 on C1 and DPR 2 with canvas 1688×780 in Garage, matching
the baseline. The requested browser context DPR 3 is not the executed render
scale. Both use the 844×390 touch viewport.

The fresh normal App run on Mac M5 Max Metal submitted 59.98 FPS for the
candidate C1 window and 60.03 FPS in Garage. C1 GPU timer samples measured
3.61 ms median / 4.81 ms p95, no disjoint queries. CPU submissions were
2.6 / 2.8 ms and rider updates 1.3 / 1.4 ms, with 11 full native resets per
submitted frame. These measurements justify the geometry candidate; they do
not justify an unrelated CPU optimization.

First Garage and the full run retained one document and its time origin.
The candidate had exactly one page fetch, answered HTTP 200 through the
service worker. Zero request failures, page errors or context loss/restoration.
Automation used navigator.webdriver and the actual audio module remained null.
The loader disappeared at 7.576 s; hero loading took 5.047 s, shaders 600 ms,
first frame 351 ms. Loader text showed 106.81 MB complete; there was no later
loader reinsertion in the retained lifecycle.

The run uses four normal 20 second windows, ordinary RAF/physics, trusted
Garage outfit buttons and held throttle. The public App flow launches C1,
bypassing only the world map. Each C1 window contains one actual crash and
automatic respawn, approximately 1.0 s after the crash. C1 was not cleared;
explicit instant restart, replay determinism and stranger attempts are not
qualified. Screenshots remain only in ignored harness output; no still is an
art acceptance witness. Raw per-frame/lifecycle samples are retained compressed.

The renderer's 577.64 MiB C1 texture statistic is a rough RGBA size estimate:
`estimateTextureMB` in `src/render/index.ts` ignores compressed mip block
lengths. It is not a measured compressed GPU allocation. The independently
verified candidate's ASTC/BC7 texture mip budget is 187,433,520 bytes; this
run did not capture runtime texture formats or allocations. Browser RAF is
uncapped on this Metal launcher and can exceed 60 callbacks/s. Submitted FPS
measures the actual production render cap.

The build is frozen private build01, stamped 1430fd83eb7da8bff955b5919c03ff26156b7e1e,
with uploaded GLB 585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef
(74,833,728 bytes), fitted profile659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972,
and compiled native metadata572476fa24f6f5f5c4bef66d7e557d9b36a983671498aa6d6c7b561c70ba0635.
Those source/profile hashes were witnessed in the ordinary rider instance.

Validation: unchanged guarded Metal command returned exit 0 in 105.359 s.
Original admission was <55 GiB anonymous and <68 GiB anonymous+wired;
original owned-run stops remained 65/96 GiB and 420 s. Anonymous maximum
54.4 GiB; sampled owned process-tree RSS maximum 3.058 GiB. No threshold
raise, foreign process kill, pose/tick/replay/camera/cap/quality override.
The original baseline uses Mac WebKit; only geometry is a matched numeric
comparison. Physical iPhone Safari sustained >30 FPS, preferably 60 FPS,
startup/first-Garage stability, memory and visual acceptance remain open.

Evidence: [compact report](run01/report.json), exact report and per-frame
samples in run01/*.json.gz, executed recipe in run01/recipe.mjs.gz, and
original guard plus pressure/swap/RSS admission telemetry in run01-guard/.
