# 3D world map movement and progress states

The [silent played WebKit capture](played-map.mp4) runs the normal menu → C island → twelve tower taps → portrait rotation prompt → landscape pan → explicit orbit → menu → C1 Ride flow at 852×393. The [machine report](report.json) has no page errors, selects the correct track at all twelve towers, and reaches the ride with the gameplay WebGL context restored.

Default drag moves the island: the tested drag shifted the camera target 12.30 map units while changing azimuth by less than 0.001 radians. The Rotate button recenters the island and changes the same gesture to orbit; the played drag changed azimuth by about 1.96 radians. Right mouse drag also orbits, and two-finger touch retains zoom and rotation. The [panned](landscape-panned.png) and [rotated](landscape-rotated.png) captures index those moments in the video.

Each tower now has a terrain-following colored ring and flag treatment: muted slate is locked, amber is available, and earned Bronze, Silver, Gold and Diamond each have a distinct color. The selected card names the state and lock rule or result. The [state comparison image](medal-state-markers.png) injects all medal variants into the renderer only for visual inspection; its `0 / 12 cleared` progress counter still reflects the test save, so it is **not** a real earned-progress screenshot. The normal first-save state in [the opening screenshot](landscape-front.png) is three available Coast stages and nine locked stages.

This is headless WebKit evidence, not a physical iPhone gesture or frame-time result. Physical landscape touch readability, sustained GPU performance and accessibility review remain open for the store gate.
