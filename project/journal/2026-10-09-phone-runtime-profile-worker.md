# Normal-clock rider phone viewport diagnosis

Finding: The selected remaster lacks an effective lightweight gameplay mesh.
The existing source-equivalent production build renders 2,581,869 hero
triangles on C1 at low quality, compared with 13,630 for the original Mustard.
Normal C1 submissions total approximately 5.26 million triangles for the
remaster versus 121,984 median for the original. This is a mobile GPU cost
candidate, not a measured explanation of the user's physical iPhone 12 FPS.

Validation: The unchanged bounded guard admitted the WebKit run and returned
exit 0 after 110.873 seconds. Four normal-clock 20 second windows measured
59.88 FPS original Garage, 60.03 original C1, 59.99 remaster Garage and 59.79
remaster C1 on this Mac with a touch phone viewport and DPR 3. The renderer
chose low automatically. No quality, cap, camera, bone or physics tick writes.
Trusted throttle ran through the actual App RAF; normal App flow launched C1.
The world map GPU transfer was deliberately bypassed and is not qualified.

Validation: Zero page errors, one main-frame navigation, unchanged time origin
across outfit choices and zero extra GLB requests during both Garage swaps.
The initial loader disappeared at 12.354 seconds; Hero models consumed 9.364
seconds, shaders 379 ms and the first frame 537 ms. No post-boot loader or
context loss was observed in this run. This is not a phone reload diagnosis.

Finding: The full native COM solver is secondary here. Actual remaster riding
rows measured 1 ms median and 2 ms p95 rider update CPU, with 14 full resets
per frame at median/p95, 38 worst. Garage was 2 ms/3 ms with 14 resets.
Original rider updates were below this WebKit's 1 ms timer precision.

Limits: GPU timer queries are unsupported in this WebKit, so GPU time is null.
The nested Garage reflection flag was omitted by the hook's sanitized render
snapshot. Do not attribute the 5.2 million triangles to a mirror. Source
reflection cap and the hero-only shadow path suggest scene plus shadow, but
that is source inference. The revised recipe captures direct debugInfo fields
on its next run; its extra witnesses have only syntax/lint validation so far.
The exact executed recipe is retained and hashed in run02/recipe.mjs.gz.

Limits: No video was encoded. Screenshots follow actual normal-clock play,
raw lifecycle and per-frame records remain compressed, and physical iPhone
sustained FPS, memory and restart behavior remain unaccepted. The first run's
output-parent mkdir setup error is retained; it exited before a browser started.

Evidence: docs/evidence/rider-rebuild/phone-runtime-profile01/run02/
