# Snowline challenge review — S1–S3

S1 Lift Line's top station now has a 22°/2.2 m lip, 12 m deck, 28 m descent and a 30 m checkpoint run-up. The [run-up sweep](runup-sweep.json) found that 20–27 m still allowed a held-GO clear after respawn; 28 m stopped both bikes, so the authored 30 m gives 2 m of margin. S2 Cornice and S3 Whiteout already rejected held GO and retain their geometry. The [120-second lane probe](held-go.json) failed on all six course/bike pairs; the [campaign sweep](../campaign-retarget/README.md) extended that to 600 seconds and three seeds.

Fresh S1 skill-3 recordings finish without faults at 29.958 s Rookie and 29.800 s Pro, with matching Node/browser hashes. Existing S2/S3 Rookie goldens still finish exactly; the S2 Pro skill run finishes at 45.950 s after three attempts, and S3 Pro at 28.625 s without a fault. The [average-rider proxy](reflex.json) finished all twelve two-seed course/bike cases in 3–12 attempts, median 6.5, with exact replay hashes; median auto-restart delay was 0.629 s. This is a simulated controller, not a touch-player study.

The [controlled S1 clip](s1-pro-controlled.mp4) lands on the station deck; the paired [held-GO clip](s1-pro-held-go.mp4) over-rotates and crashes. A [held-GO S2 clip](s2-pro-held-go.mp4) shows its failed gap. All are silent played browser captures at 852×393 with camera-box passes in [played-clips.json](played-clips.json).

The [route feasibility record](route-feasibility.json) finds no qualified Pro-favored Diamond route. Current Pro advantage is only 0.5% on S1 and 2.7% on S3 in the sampled clean lines; on S2 the sampled Pro run is slower and faulted. The rules currently tighten Pro's medal clock by 10%, so these results do not support selling the second bike as a late-game medal shortcut. New phone players and a distinct upper traversal remain open.

Reproduce with `pnpm exec tsx harness/snowline-probe.mts`, `harness/snowline-reflex.mts` and the checked-in recordings. Source is `src/tracks/rockhop/snowline.ts`; no release promotion follows from these bot results alone.
