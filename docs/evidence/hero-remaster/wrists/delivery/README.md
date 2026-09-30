# Wrist repair in the actual game

Parent verdict: accept the repaired Street wrist surfaces on full and phone
LOD. Both forearms stay connected to their gloves during the Garage rotation
and played riding sequence. V5's detached ends and blue wedges are gone.
Skin colouring and close-up shape/shading still need M1/M2 art work; this is
not acceptance of the complete remaster or physical-phone performance.

[Garage before/after movie](garage-ab.mp4): **left V5, right repaired V6**.
Both are actual Menu→Garage captures with matching runtime, camera, lighting,
and every non-rider asset SHA. Only the two Street model hashes differ.
[High-detail ride](ride-high.mp4) and [phone-LOD ride](ride-low.mp4) use the same
recorded inputs for 1,440 ticks, with no injected mesh/bone pose. Camera follows
the actual wrists. [Normal-build phone orbit](normal-phone.mp4) verifies the
ordinary public model paths, complete hero visibility and Garage entry.

Movies are silent. Garage captures use the host presentation clock while
physics stays frozen; capture cadence is not an idle-speed or frame-pacing
measurement. Some extreme detail-camera angles crop a hand; the full-frame
rides, full Garage orbit and explicit complete-contour gate complement them.
`review.json` records source captures, served hashes, bounds and parent verdict.

The full export is `bbf2d636…`: 57,773 triangles, 4 draws, 1,442,236 bytes.
LOD is `def6821d…`: 7,837 triangles, 4 draws, 530,340 bytes. Both are promoted
into `public/models` and the retained delivery mapping on main. The other
riders and the production bikes retain their existing geometry; V5 bike
candidates remain separate. Full adds one draw and 2,336 bytes versus V5;
LOD saves 34,960 bytes. Both stay within 60k/8k and eight-draw ceilings.

The [independent seam gate](../v6-seams.md) checks all eight closed contours,
consistent winding, bind-aware skin coefficients and 3,759 world-position
correspondences through seven cases per tier. All seam, weight and coefficient
errors are exactly zero. No selected wrist or repair triangle collapses. These
CPU pose probes are synthetic; the movies supply played engine evidence.

The fragmented V5 LOD had no usable forearm contour. A clean full-derived body
reduction replaces it, retaining the authored LOD contact and hair meshes
exactly. Generated head surface deviation is 3.6–4.6 mm p95 versus V5 LOD;
source preservation and deviation reports are in the rider-generation folder.
The full repair preserves non-wrist attributes and original clips; sixteen
inherited zero-area donor triangles are removed by index only.

`replay.json`: normal-build low/high clears both finish at tick 4810,
40.083333333333336 seconds, zero faults, canonical hash `368f1ca5bd9e830a`,
identical Float64 bytes `abaaaaaaaa0a4440`. Forced crash occurs at tick 103;
restart returns to riding at tick zero in one update (1 ms host measurement).
`swaps.json`: twenty cached family swaps, bounded resources, no page errors.
A bot and host WebKit do not close stranger or sustained iPhone gates.

The shipped-asset regression runs in `src/render/hero/wristSeams.test.ts` with
committed packed correspondence maps and no ignored raw-master dependency.
Old Street cloth triangle IDs now exercise the unchanged Charcoal body, whose
position/index/weight buffers match the prior Mustard body exactly. Stage
checks verify the delivered optional neck idle as well as protected contacts;
other outfits retain their static seated clip. The geometry conditioning test
preserves inherited neck/head weights while checking the smoothed sleeve
fraction; position quantization can co-locate distinct inherited neck points.
