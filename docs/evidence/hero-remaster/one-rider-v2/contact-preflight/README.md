# Visible contact probe preparation

Status: CPU helper verified on synthetic posed geometry. No new rider mapping, real rider contact result, gameplay clip, or visual gate is accepted by this work.

`harness/hero-remaster/surface-contacts.mts` measures explicitly selected visible palm/sole surface patches after the live pose. It uses Three's `SkinnedMesh.getVertexPosition`, including morph positions, skin weights, inverse binds, attached/detached bind handling, then the mesh's current `matrixWorld`. The four independent slots are `hand.L`, `hand.R`, `foot.L`, `foot.R`. It never selects geometry by bone proximity or dominant weights, and never substitutes bone/socket origins for the skin surface.

An external `SurfaceContactManifest` must bind the four reviewed surface patches and bike target primitives to the SHA256 of the actual fetched rider and bike GLBs. Each patch also identifies an exact child-index path plus node name and the SHA256 returned by `runtimeSurfaceSHA256` on the prepared runtime mesh. That digest includes runtime positions, indexing, skin indices/weights, inverse bind matrices, bone order, bind mode/matrix, and position morph targets. GLB accessor indices alone are insufficient after model merge and sleeve conditioning. A changed model, runtime geometry object or tier requires fresh preparation and the corresponding reviewed mapping.

The external mapping provides triangle ordinals, or explicit vertex indices plus incident triangles for normals. Its review evidence must show that those triangles/vertices are the actual exposed palm or sole. Every target supplies a live bike-object frame, finite capsule/cylinder axis and radius, and evidence that the primitive matches the visible grip/peg. This helper does not manufacture those definitions. The production procedural peg is a rounded box; a cylindrical approximation is not automatically accepted as its real surface. If the chosen visible peg cannot be represented accurately by a reviewed primitive, add a separately tested triangle/box target rather than claiming the cylinder is exact.

Unsigned gap alone hides penetration. Each measured slot therefore reports minimum/maximum signed point-to-primitive separation, smallest absolute gap, deepest sampled penetration, nearest sample and target world positions, posed normal mismatch and maximum triangle lattice spacing. Positive signed distance is outside the primitive, negative is penetration. Normal mismatch compares the outward character triangle normal with the opposite outward bike normal. Triangle patches use a barycentric lattice; vertex patches only cover listed vertices. There is deliberately no automatic pass flag.

Missing, unreviewed, stale or invalid definitions produce `status: unmeasured` and a reason for that slot. They produce neither zero distances nor a pass. Hidden mesh ancestors, degenerate posed triangles and nonuniform/sheared primitive frames also remain unmeasured. The nearest-gap result cannot prove that the full palm/sole area makes contact: a single sample may touch while another part floats. Inspect separation range, patch coverage, penetration, normals and moving footage together. Lattice sampling may miss sub-sample intersections; it is not a continuous triangle/solid collision solver. Geometry/material visibility, camera occlusion, self-intersection, finger wrapping and rider anatomy still require visual review.

## Private capture integration

Do not import this module only into Node and expect Playwright's serialized `page.evaluate` function to retain it. Bundle the helper into the isolated harness build or load a separately bundled browser module. Expose that module under a private harness handle; no generic player path was changed here.

1. Prepare only after `hero-capture.mts` has completed its quality selection and `r.whenReady()`, using the LIVE clone roots `r.debug.rider.root` and `r.debug.bike.root`, not `source.scene`. Await `__assetProof.pending` and take the matching SHA values from the actual consumed model URLs. Record manifest bytes and hash with the capture's frozen build inventory. The catalog alone is not consumed-byte evidence.
2. Call `prepareSurfaceContacts(mapping, { rider, bike }, consumedHashes)` once per settled rider/bike/tier. It hashes reviewed runtime geometry without posing the character. Pose input and physics remain untouched.
3. In the existing capture loop, call `probe.sample()` immediately after `t.render(true)`/`gl.finish()` and rendered-time equality, where the current harness reads `boneOrigins` and `jointWorld`. Add the result as `surfaceContacts` in each trace frame. Keep the existing exact state JSON/hash, segment tick, global input tick and rendered time. The helper only updates Three world matrices and reads deformed geometry; it changes no inputs, physics state or joint transforms.
4. Preserve prefix playback: every preceding frame must be played/rendered from input tick 1. Never start at a landing's reset segment tick. Keep crash/ragdoll surface distances in the trace, with phase/ragdoll context; deliberate crash detachment is evidence, not automatically an IK defect.
5. Add a private CLI mapping argument (for example `--surface-map /absolute/map.json`) without changing existing positional arguments. Record a missing mapping as unmeasured; require all four mappings before claiming the new rider's contact gate is tested. Re-prepare on any tier/model/geometry switch. At 120 Hz use 120 fps to sample every listed centre tick; at 60 fps round the clip boundaries outward and disclose that odd centre ticks are not exact rendered frames.

Existing `gltfRider.ts` sockets remain useful for IK diagnostics. `SOLE_ON_PEG` places the sole socket 11mm above the peg axis, and `hero-capture.mts` currently records bone origins. Neither proves an actual sole/palm surface gap. Do not reuse an old 20mm origin tolerance as a visible-surface pass. The parent must judge the requested visible contact bar with the new mappings and played footage.

## Matched windows

These are the current manifest's global input ticks, not resettable physics ticks. Recordings below live in `docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/`. Read and hash that manifest again when executing; this table is a preflight aid.

| Case | Recording basename | Start | Centre | End |
|---|---|---:|---:|---:|
| Rookie maximum forward lean | riding-poses-lean-transitions-rookie.json | 283 | 343 | 463 |
| Rookie maximum backward lean | riding-poses-lean-transitions-rookie.json | 523 | 583 | 703 |
| Rookie front landing/recovery | e2-rear-wheel-first-bot-3.json | 4483 | 4543 | 4663 |
| Rookie rear landing/recovery | e2-rear-wheel-first-bot-3.json | 2560 | 2620 | 2740 |
| Pro maximum forward lean | riding-poses-lean-transitions-pro.json | 281 | 341 | 461 |
| Pro maximum backward lean | riding-poses-lean-transitions-pro.json | 522 | 582 | 702 |
| Pro front landing/recovery | c1-low-tide-bot-3-pro.json | 1168 | 1228 | 1348 |
| Pro rear landing/recovery | e2-rear-wheel-first-bot-3-pro.json | 4728 | 4788 | 4908 |

Pro E2's 4788 global input tick is physics tick125 after earlier resets. Its full recording has16 faults and ends riding, so this remains an impact/contact diagnostic, not a clean clear. The earlier E2 prefix is insufficient for this selected event. Recovery currently means uninterrupted riding for the following second; it does not prove fully settled velocity or pose. Run both bikes, high and low tiers, matching baseline/candidate build, camera, cadence, input bytes and consumed GLB proofs. Compare exact physics trace/finish bytes separately from this visual geometry measurement.

## CPU validation

`pnpm exec vitest run harness/hero-remaster/surface-contacts.test.ts`: 9 tests passed. They exercise finite cylinder sides/caps/corners, capsule hemispheres, penetration, nonidentity world/bind transforms in attached and detached modes, blended bone weights with a stationary root, position morphs, posed normals, explicit vertex patches, stale hashes/geometry, frozen mapping definitions and rejected nonuniform primitive scale.

`pnpm exec tsc -p tsconfig.harness.json --noEmit` and focused `pnpm exec oxlint harness/hero-remaster/surface-contacts.mts harness/hero-remaster/surface-contacts.test.ts`: passed. No browser/GPU run occurred. No source in `src/` or existing capture path changed. These unit outcomes prove the helper's exercised math, not the new character's contacts or appearance.
