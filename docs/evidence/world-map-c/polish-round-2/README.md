# Selected C island: second standalone polish pass

## Evidence

- [Silent played 360° orbit and 12 tower taps (MP4)](played-orbit-and-12-taps.mp4); [raw capture](played-orbit-and-12-taps.webm)
- New art views: [front](front.png), [three-quarter](three-quarter.png), [reverse](reverse.png)
- [Portrait rotate prompt](portrait-rotate.png) and [measurements](measurements.json)
- Before this pass: [first-pass orbit](../polish-round/played-orbit-and-12-taps.mp4), [front](../polish-round/front.png), [three-quarter](../polish-round/three-quarter.png), [reverse](../polish-round/reverse.png)

The route now has shallow, color-matched shoulders rather than a raised dark-bordered ribbon. Forest silhouettes mix pines and broadleaf crowns around a timber lookout and a waterwheel at the sawmill fall. The harbor gains a painted lighthouse and fishing traps; the quarry has a mine headframe and ore; the snow side has a rescue roof and glacier-blue fractures. Small static props are merged by material after construction; the 12 selectable flag towers and dynamic beacons remain independent.

At 852×393, DPR 2, SwiftShader: **12/12 physical pointer taps** selected the correct tower, the portrait view showed the rotate prompt, and there were zero page errors. Front/reverse views rendered **612 calls / 460,507 triangles**, compared with the first pass's **922 calls / 469,183 triangles**. The static batch merged 350 source meshes into 59 batches. Headless software-renderer samples remained about 4 FPS; the draw-call reduction does not establish iPhone frame rate, memory, or thermal behavior.

The moving orbit and three angles are more composed than the first pass, but the broad cliffs and conifer forms still have procedural repetition. This remains an isolated prototype: Ride is a stub and the real game still has the prior production map. It is not an App Store-ready asset or validated mobile renderer.

Reproduce with the prototype Vite server on port 5178: `ATLAS_OUT=docs/evidence/world-map-c/polish-round-2 node prototypes/world-map-c/capture-polish.mjs`. The MP4 is a trim of renderer startup from the raw WebM, encoded with H.264 for mobile viewing.
