# C island: glacial massif and cliff color pass

The [silent played orbit and twelve tower taps](qualified-orbit-and-taps.mp4) use the real review selector at 932×430 landscape, DPR 2. The camera turns from touch drags. The [front](qualified/front.png), [reverse](qualified/orbit-3.png), and [852×393 phone overview](phone-overview/front.png) frames are captured from live sessions. The visual target is the [selected C island](../orbit-round4/selected-reference.jpg), with the [prior played orbit](../orbit-round4/qualified-orbit-and-taps.mp4) as baseline.

The prior far-right snow massif read as three smooth white cones. I rebuilt those peaks with asymmetric, faceted ridge geometry and an irregular snowline. The exposed coastline now uses biome-specific fractured rock color rather than a uniform charcoal rim, and its existing instanced buttresses have a lighter mineral palette. The road and twelve selectable towers were not moved. An experimental thin coastal ledge was discarded because its broken line read as decoration at phone scale.

The [measurements](qualified/measurements.json) show 12/12 tower taps selecting C1 through S3, zero page errors, 294–297 draw calls and 449,621–449,897 triangles. The baseline had 293–297 calls and 449,105–449,393 triangles, so the final model adds about 500 triangles with no sustained draw-call increase. The post-load orbit ran at 4–5 fps in headless SwiftShader at DPR 2; this is not a physical iPhone measurement.

At 852×393 the top detail card covers part of the rear forest crown and industrial skyline, but leaves the road and all twelve tower signs exposed. The remaining gap to the selected image is model finish: broader snow ridges, richer cliff sculpting and higher-quality village props. This pass is evidence for an art iteration, not approval to replace the production painted map yet.

Reproduce with [capture.mjs](capture.mjs) against the [round-three Vite config](../orbit-round3/vite.config.mjs): `node docs/evidence/world-map-c/next-art-round/capture.mjs qualified 5184 2 --taps`. Add `--viewport=852x393` for the smaller landscape view. The MP4 is H.264/yuv420p and contains no audio stream.
