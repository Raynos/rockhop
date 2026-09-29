# Map drag after selection

The [played landscape capture](played-map.mp4) follows a fresh load through all twelve tower selections, a drag immediately after the last tower focus, the Rotate overview, portrait prompt, ordinary pan and orbit, then C1 Ride. The [headless WebKit report](report.json) passes with zero page errors and 12/12 correct tower selections.

The first drag after a focused tower moves the camera target from x=16.62 to x=14.46 while azimuth stays 0.083 radians. Rotate cancels the focus move, recenters on the island and pulls back to distance 38 before orbiting. Leaving the map resets the gesture to pan; reentering after portrait also starts in pan mode. The played capture shows the focus and resulting pan rather than a posed view.

The host WebKit sample after 1.2 seconds reported 48 fps, 280 calls and 414,554 triangles at 852×393. This sample is not a sustained device benchmark. Physical iPhone gesture feel and GPU performance remain open in the release gate.

The [four-section host Metal gate](ship-gate-partial.json) passed 11/11 cold boot, clear, crash and instant restart checks after this interaction change. It is a partial gate, not a store-release verdict.
