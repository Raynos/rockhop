# Conservative A2/A3 shared-bank rollout candidate

Reduced-scope lane: reuse the existing Alpine phone model/maps and existing
mill/log/loader geometry. This source slice adds no machinery, textures or
public bank. A1 keeps its accepted 55/221-anchor forest and quieter materials; these helpers address A2/A3 continuity.

`src/render/world/zones/alpineForest.ts` is unimported. It verifies each course's
seed/collider hash, GPU Float32 source tree signatures and matching contact
shadow count before removing anything. The source hash derives from actual
current builders, not copied screenshots or independently rerun scene RNG.
`anchor-audit.json` records the input source hashes and conservative forest
costs. A2 has 51 near/215 far originals; A3 has 59 near/209 far originals.
The audit retains add-time item references before buildBatches splits foreground
items into occluder meshes. Browser/Node trig may differ by one Float64 ULP, so
signatures use Float32 GPU precision while exact original matrices stay unchanged.
Roots use exact zoneGround minus 4 cm, with the original x/z/yaw anchors.
Close hazard and foreground crowns become low regrowth; A2 retains denser
mixed stands while A3 uses younger trees and snags. Near clusters span 48 m
bins, split foreground/background, and two permanent far atlas banks retain
the original distant anchors. Visual clearance remains a played judgment.

## Parent integration contract

Inside the existing authored-course guard, after the original ZoneKit has
generated every original prop and therefore consumed its normal scene RNG:

1. Call `planAlpineForest(track,zk.batches)` before mutation.
2. Call `removeAlpineForestPlaceholders(track,zk.batches)`; its `originals`
   are dedicated fallback batches containing the **same** removed item objects,
   geometry, material and shadow flags. Add buildBatches(originals) to a visible
   fallback root. Remove no other family or contact shadow.
3. Mount `loadAlpineForest(plan,{completeMaterial: m=>lib.complete(m)})` using
   the current course owner. Parent gives meshes `props:*` shadow naming as for
   A1. Hide only this course's fallback after successful live attachment.
4. Retain existing owner cancellation, entry warmup, library completion and
   renderer retirement. Required-map errors and late loads use the same
   proven existing Alpine kit. Failed validation leaves all source items intact.

Both courses reuse the same staged full/near geometry and fourteen phone maps;
no desktop bank is decoded. `banks:'far-only'` loads only the existing atlas
maps and produces three draw banks for the whole forest. The normal option
shares all variant geometry/materials across clusters, with 26/65 m LOD limits.
Whole-course draw bounds and shadow bounds are proposals, not GPU measurements.
Do not relax the 700 KiB player or resource/frame budgets to integrate them.

## Checks and remaining review

Twelve focused tests exercise actual seeded source builders, atomic validation,
dedicated item-identity fallback, exact ground contact, deterministic placement,
foreground height, cancellation, failed mounting and far-only allocation.
Run `pnpm exec vitest run src/render/world/zones/alpineForest.test.ts` and
`pnpm exec tsx assets/blender/course-kits/alpine-trees/audit-rollout.mts`.
The fixture stubs Canvas/art pixels and calls normal main builders in Node.

No shared biome hook or public bytes are activated. The first private frozen
pair passed both budgets but failed the source guard and retained originals;
`prototypes/alpine-forest-rollout-v1/startup-failure-proof.json` records the
audit defects and corrected source checks. A fixed moving trial remains open. Parent must review matched full
rides and log-pivot/beam/loader fault/recovery views at 852×392 low tier, with
the same rider/input/camera/physics and actual bank hashes. Keep the current
log top, teetering motion, beam contact, loader pose and silhouette readability.
Remaining work is material/contact coherence using existing models, not a new
bespoke asset family. Full art acceptance and physical-device review remain open.
