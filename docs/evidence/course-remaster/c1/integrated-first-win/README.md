# C1 integrated first win — frozen WebKit proof

[Watch the uninterrupted 852 × 392 ride](played-flow.mp4) · [Read the machine report](report.json) · [Rerun the harness](../../../../../harness/course-remaster/c1-integrated-first-win.mts)

The 41.7-second silent video follows one App page from Menu through the default 3D world map, C1 tower selection, a complete clean Rookie ride, the actual finish report, Map, Garage, reload, and the map with the saved medal. Its first result is **Diamond, 0:30.350, +300 Scrap**. The Garage displays 300 Scrap; after reload, the saved C1 map marker is `platinum` (the stored name for Diamond), and the wallet remains 300.

The pinned input is `harness/inputs/c1-low-tide/bot-3.json` (SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`). Both Node and the live WebKit App finished at tick **3642**, time **30.35 s**, zero faults, state hash **`2bfe061963ffb058`**. After filming ended, the harness ran the identical ride on the same reloaded page. Its second Diamond report said **“No new Scrap”** and the wallet stayed 300. That repeat is in the JSON, not the MP4.

The game source came from an isolated `git archive` of commit `0e75f4159e5c6183f213489b4dd5bf23345a84f2`; no uncommitted app files were included. The new harness script was copied into that archive. `report.json` records the source tree, private build, harness, input, and video hashes. The video is H.264, 20 fps, 834 frames, 8.7 MB, with no audio. The report records zero page errors and zero console errors.

This is scripted headless WebKit evidence at landscape phone geometry, not a stranger or physical iPhone run. The harness uses the real Menu, 3D map and Ride touch targets, then steps the pinned 120 Hz input while rendering every video frame. It skips the final countdown fraction to align the recorded input exactly. Service workers and audio are disabled. The frozen commit excludes subsequent uncommitted art; this proof establishes integrated flow, persistence and repeat-payout behavior for the named commit, not mobile frame rate or final art quality.
