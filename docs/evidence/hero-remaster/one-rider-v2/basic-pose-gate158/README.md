# Basic-pose gate foundation — round158 / ask248

Status: **unaccepted exported rider; executable CPU coverage established**.
Parent owns this harness and integration. Task-3 owns construction repairs under
`foundation-repair-task3`; this round reads its inspected motion source and frozen
rest centres without altering them. Cosmetics remain paused.

The fixture covers12 bilateral families at24fps,97 samples each: neutral,
horizontal/overhead/forward arms, elbow, forearm twist, wrist flex/deviation,
grip, squat, sit and lean. Each family returns to exact neutral. Original source
grip morphs alone are admitted; V6/V7 authored49compression shapes are disabled.
The Three.js player maps declared19names explicitly and derives local transforms
from desired world deformation and retained rest transforms. It rejects unknown
bones, mismatched centres, nonfinite values and ambiguous aliases.

Actual mappedV5 GLB passes1,164 samples of stock Three.js skin evaluation over
25,352 body/hood vertices. World/local parity max1.333e-15; neutral endpoints
return within1e-5m and source/fixture hashes remain unchanged. Frozen controls
preserve all upper/lower limb lengths within8.89e-16m. These verify the test
mechanism, not anatomy, clothing or appearance.

Failures remain: body/hood quarter-area collapse peaks260 faces overhead,103
elbow,256 squat and255 sit. Neither zero collapse nor legal matrices can pass
appearance. CPU loading omits image pixels and does not measure glove/cuff joins,
self-collisions, volume, contacts or rendering. Gray/PBR moving films, unilateral
controls, held-out halfsteps, actual Garage/gameplay and mobile remain UNMEASURED.

The first lower fixture exposed a bad authored knee pole:104mm adjacent sit
surface motion. Its source and CPU report are retained. A different transverse
source-knee-plane pole reduces the sampled maximum to15.38mm; this is a fixture
correction, not a character repair or visually accepted animation.

Recipes: `harness/hero-remaster/basic-pose-gate/generate.py`, `inspect_fixture.py`,
`protocol.ts`, `run.mts`. `fixture-provenance.json` pins source controls and private
fixture; `v5-cpu-v3.json` retains every tested sample and open gates. No player
asset is promoted. Next: moving gray/PBR review with the same exported fixture,
then qualify the independent construction candidate through this interface.
