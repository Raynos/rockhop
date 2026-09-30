# A1 quiet material pair — moving candidate retained by parent

Source checkpoint `4d1c528b`; actual paired graph frozen at
`7fe59bc9c362de1b4a7036769e0d7071b3178d6b`. Both sides contain the accepted
55-near/221-far A1 botanical forest and identical app/public/harness inputs.
Only the recorded biomeKit/zoneDeck material overrides differ. The parent
reviewed the full/flume sequences and retained the quieter ground for rider
and hazard separation; broad soil still reads soft. No more cosmetic iteration
is requested. Whole-course art and device acceptance remain open.

Before is left, candidate is right:

- [Full ride](full-compare.mp4) — 365 frames, 30.35 s clear, exact tail `397beb1fcd345e2d`.
- [Flume fault](flume-fault-compare.mp4) — 106 frames, exact tail `9b8c25c5404681b3`.
- [Exact restart](fault-restart-compare.mp4) — 125 frames at 120 FPS, exact tail `4b9a060e15075b4a`.

All six captures are silent headless Metal, low quality, 852×392, the same
Rookie recordings/camera/physics. Camera checks pass and the full forest mounts
exactly once in both phases. Original capture JSON and contact sheets are
included by phase/case; raw clips remain ignored under ../out/. Sheets index
the played clips and are not independent art evidence.

| Proof | Before | Candidate |
| --- | --- | --- |
| Player gzip bytes | 714,077 (697.34 KiB) | 715,349 (698.58 KiB) |
| Raw inline loader | 8,175 B | 8,175 B |
| Actual entry JS SHA | `2aacd37c4e7558a69371e52caa216d091ac60cb9c48065cd2eb835e65565c2a8` | `344332e22eef754bae71f33219edfc86998a9ff25d37b3ee1d780b882f6af253` |
| Model/resource catalog SHA | `2d9e63e82e4610b1033f15ea1c1c56fb29c17473cb6a9cd021c3739b521d6467` | same |

Both ordinary Vite builds pass unchanged 700 KiB player / 8 KiB raw inline
gates. Actual post-build generated tables match. `provenance.json` and each
paired report preserve build hashes, all replay hashes, clip hashes, Metal
renderer identities and the dirty live-tree context. Concurrent main/hero work
was excluded by full frozen source/bank inputs. No timed perf run was made;
entry counters captured under concurrent load are not comparative timing proof.

## Allocation concern checked: no per-chunk texture replication

The frozen deck.ts calls buildZoneDeck **once** per buildRideSurfaces, then
chunks each returned geometry with chunkByX and constructs every chunk using
that same material (`new THREE.Mesh(g,m.mat)`). The private hook calls alpineSoil
once for tread and once for bank, before chunking. The detached ZoneKit hook
calls it once for terrain floor and adds one lake normal. There are **seven
new CanvasTexture objects per world**, not seven per 40 m chunk.

Gross per-world allocation remains 3.667 MiB with mip estimates: tread/floor
each 512² albedo+128² normal, bank 512×256 albedo+128² normal, lake 128² normal.
The maps are already shared by all surface chunks. Each new world owns its
material sets; a persistent per-library role cache would require eviction on
course retirement to avoid returning disposed Canvas maps to a later world.
No such cache or ownership expansion is needed here. Shared neutral maps are
DataTextures and are never disposed by the candidate Canvas retirement path.
The detached terrain clone is released without disposing borrowed library maps.

The actual full-ride resource loops now supply whole-scene reported maxima:

| Resource | Before | Candidate |
| --- | --- | --- |
| Texture estimate maximum | 45.630 MiB | 44.630 MiB |
| Texture object count maximum | 97 | 100 |
| Calls p95 / maximum | 97 / 101 | 97 / 101 |
| Triangles p95 / maximum | 93,883 / 97,315 | 93,883 / 97,315 |
| Geometry object maximum | 229 | 229 |

Both loops sample the same full recording at 20 FPS (607 samples), clear at
30.35 s and end at `91f3878cfca365d6`. That endpoint uses a different tail tick
than the visual clip, so it is compared only to the other resource loop.
[Resource summary](resources.json) and each phase's resource-loop.json retain
the actual samples. `texturesMB` is the renderer's scene/hero-pool estimate:
it deduplicates texture objects, counts ordinary textures by image size/type
and mip allowance, and counts art textures with deliveredBytes by compressed
delivery size. It is **not** a driver resident-memory measurement or a count
of every unbound cached library texture. The lower candidate estimate reflects
different material bindings; gross new-map allocation is not a net scene delta.

The existing [missing-map and late-switch proof](lifecycle.json) passes **2/2**
against this exact frozen candidate. A failed required branch image leaves the
three original forest fallback meshes visible with mounted0. The delayed A1
GLBs resolve after D1 is active, leave owners empty/mounted0, and release their
resources: geometry disposal count 534→913, texture disposal count 137→163;
reported active-scene texture estimate remains 39.543 MiB. The supplementary
lifecycle harness source hash is recorded; it runs against frozen harness
libraries and verified entry bytes. No neutral-map ownership change was made.

Raw timings remain in the resource loops but are explicitly **unqualified under
concurrent load**. Quiet timing qualification remains serialized by the parent
on the combined accepted build. Soft soil,
mill/obstacle timber finish, distant canopy and lake fog/shoreline coherence
remain limitations; the reduced scope reuses their existing geometry/assets.

## Normal A1 integration

The parent retains this as a bounded material/readability improvement and
applies the same overrides in normal `biomeKit.ts` / `zoneDeck.ts`. Geometry,
colliders, tree anchors, physics, camera, public model bytes and the seeded
scene remain unchanged. App typecheck and scoped lint pass. A fresh normal
build passes at 698.55 KiB player JS; the required A1 boot/clear/Pro-clear/
crash/instant-restart/bundle check passes 14/14, including exact A1 finish
30.349999999999998 and pinned hash `91f3878cfca365d6`, plus C1 and D3 Pro
references. This is a partial host gate, not a release verdict.

The entry snapshot contains transient warmup render totals above whole-frame
limits; sustained ride resource maxima are the stated 101 draws/97,315
triangles. Driver residency and landscape-phone pacing remain open. This
material pass does not sign off A1 or close the twelve-course plan. No
deployment or physical-phone approval is claimed.
