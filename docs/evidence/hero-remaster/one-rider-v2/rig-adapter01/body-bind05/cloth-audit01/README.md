# Garment distortion is present in actual skin geometry

Two matched40s replays use the same WHITE body05, corrected private contact
adapter, physics input, camera and lighting. The second removes only rider
textures and uses neutral-gray material. All480physics states, ticks and
contact diagnostics are exactly equal. Actual neutral geometry still has
shoulder holes and a flared, broken hem. Texture repaint is not the fix.

CPU audits four actual recorded states through the production GLB decoder,
GltfBike and private GltfRider. Only native glove primitive1 is excluded;
primitive2 is the NEW hood and is included. Removing generic sleeve skin
conditioning does not remove the worst waist defect. At tick4210 an edge
stretches22.280times: adjacent source vertices atZ.7975/.8019 switch from
31.6percent thigh/68.4percent pelvis to100percent pelvis. The authoring
branch stops atZ.80 before its smooth blend finishes atZ.835. A separate
shoulder branch switches upper-arm influences abruptly to chest atZ1.43;
source-weights shoulder stretch reaches13.234times. Armpit transitions
also stretch and need inspection after the first localized correction.

Parent inspected the four defect samples and ordered1second samples across
all40seconds for both materials. No claim every480frame was visually judged.
Keep the WHITE character and fix localized weights, not generator topology
or texture paint. Rest shape, bind matrices, morphs, UVs and PBR are protected.
This is an unaccepted checkpoint, body/face quality still below7in-engine.
Actual hand/sole surfaces, Garage, Pro and realLOD remain open.

Validation: CPU actual-state audit,480matched state/debug parity, harness
typecheck and lint pass. GPU capture serialized with canonical lock,180.763s
whole batch,41.068GB peak anonymous. No normal player, physics or bike edit.
