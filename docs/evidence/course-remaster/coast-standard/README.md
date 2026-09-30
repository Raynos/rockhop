# Coast working-harbor standard — isolated candidate

Status: **first integrated C1 candidate rejected in full played review**. The source handoff originally owned only
`src/render/world/zones/coastStandard.ts` and its CPU audit. The parent later
integrated C1 privately and recorded the rejected played comparison below.
Production hooks are restored; no device pass or course sign-off is claimed. The CPU R3 p50 gate remains red independently of this art work.

## What the full rides show

The played C1 [full sheet](../c1/coast-wide/after/full-sheet.jpg), C2
[full sheet](../c2/pier-art/after/full-final/sheet.jpg), and C3
[full sheet](../c3/breach-art/after/rookie-full/sheet.jpg) show the same visual
pattern for most of three rides: a broad, pale quay, repeated tire/container
clusters, a bright featureless sea band, and detailed photographic freighters
far behind small procedural vessels. The authored [C1 tug](../c1/harbor-tug/README.md)
and the C2 pier/C3 breach pieces improve individual moments, but do not make a
consistent dimensional harbor. The photo vessel at `z=-200` is still the
dominant shape. This is a whole-course issue, not a missing single hero prop.

The current source explains that read. `zoneKit.ts` builds Coast terrain from
one 4 m x-grid, places a flat water rectangle from `z=-15` to `-205`, adds
transparent circular foam, repeats 12 m quay/fender modules and 2.4 m scrap
slots, then seeds procedural cranes and hulls. `biomeKit.ts` repeats a
`2048×512` photo ship plate every 720 m at `z=-200` as unlit geometry. These
systems use one shared RNG stream. Replacing them **after** their old placement
calls have run preserves all later seeded scenes; calling the shared RNG from
the new kit would not.

## Art target and route ownership

The Coast needs one coherent manufactured material language: salt-whitened wet
concrete, painted/rusted steel, soaked timber, black rubber fenders, a dark
tidal channel and a short bright break line where water meets the strand.
Near surfaces must show believable support and contact. Detailed ships,
cranes, warehouses and barges should be actual lit geometry in the near and
middle distance. The far image may carry sky, weather and horizon haze only;
it must not carry detailed ships competing with the modeled ones.

| Course | Repeated kit plus its own landmark | Protected gameplay read |
| --- | --- | --- |
| C1 Low Tide | Tidal repair apron, connected quay face, service sheds, a proper work freighter; retain the separately authored tug. | Keep `x190–258` open so the brake board, pallet ramp, container landing and tires stay legible. |
| C2 Crane Hop | Pile-supported piers, 3D barge and mooring hardware, the existing flight crane with one supporting dock crane. | Keep Pier 2 `x96–145` and final jump `x282–342` free of near/mid clutter; landing fascia must still meet its actual collider. |
| C3 Hull Breach | Beached salvage shore, a dimensional offshore work ship, connected surf and wet beach beneath the real landing. | Preserve the existing ridden hull/bulkhead and its `x272.52` lip. No detached faux beach ramp or model blocking the breach flight. |

The source candidate provides continuous `groundAt`-following terrain, quay
face, pilings, deterministic shore/water contact, sparse service hardware and
three course-specific dimensional landmark families. The ridden `zoneDeck`
and `obstacles.ts` remain authoritative. A visible slab or foreshore never
creates an implied new rideable surface. The new material kit owns compact
base-color, normal and packed roughness/metalness maps, with AO mainly baked
into vertex color; water is one opaque mesh with one slowly scrolled normal,
and surf is one narrow shore ribbon, not screen-sized transparency.

The procedural landmarks are an isolated **model candidate**, not a claim of
AAA finished ships. The complete rendered ride must decide whether their
fair hulls, deck gear, glazing, crane foundation and service bays survive
phone-scale judgment. If they do not, replace these particular meshes with
Blender full/LOD GLBs while keeping the terrain, contact, material and
placement contract intact; do not restore the detailed photo freighters.

## Integration contract

`planCoastStandard(track,x0,x1)` makes stable keyed placements from track id,
track seed and fixed segment numbers. It does not take or advance `ZoneCtx.rng`.
`buildCoastStandard(plan,{lib,detail,groundAt})` returns ZoneKit-shaped
`meshes`, `batches`, `textureBytes`, `scroll`, plus owned resources and
`dispose()`. `COAST_STANDARD_REPLACE` names the legacy mesh/batch families to
drop after `buildZoneKit` has consumed its usual RNG. A parent-owned hook
will call `buildZoneKit` first, extract C1's tug fallback from
`c1-inshore-coaster`, replace the listed families, append the new kit, and
only hide the legacy fallback after a live authored asset is attached. The
still-useful C1 brake board/winch/derrick and C2 pier art stay. C3's ridden
ship lives in obstacle art and stays. The parent-owned backdrop hook must
remove the Coast photographic plate in favor of sky/weather only; leaving it
would defeat the kit even if the geometry were good.

Specifically, the `biomeKit.ts` exterior branch currently creates sky only
inside `if (plateTex && skyTex)`. For Coast, that branch must allow `skyTex`
alone, create the existing sky plane, skip the Coast plate plane and its
`2048×512` texture accounting, and remove Coast photo plates from the offline
plan once the new scene is accepted. Do not merely hide the plate behind a
second layer. At the ZoneKit call site, filter the listed `zk.meshes` and
`zk.batches` **after** the x149 tug fallback has been extracted; do not skip
`buildZoneKit` or alter its `rng` calls. Append candidate meshes/batches and
count candidate textures. The old foam map and other discarded local resources
need disposal without disposing shared library maps. The parent must carry
`disposeMaps()` into `ThreeRenderer.clearWorld()`'s retired-world callback:
the current generic traversal disposes geometry and owned materials but only
auto-disposes `CanvasTexture`, while this kit owns `DataTexture` maps.
Candidate materials have empty names so they participate in the renderer's
material-program retirement wait. `dispose()` is available for standalone
failure/cancellation before the world takes ownership.

All added objects and maps are owned by the course and disposed on retirement;
none mutates shared `MaterialLibrary` materials. Runtime meshes use the
existing fog hook and `PropBatch` chunk/LOD rules. There is no model fetch in
this first isolated candidate, so it remains offline after the base pack.
An authored Blender full/LOD landmark could later replace each procedural
silhouette through `mountCourseAssets` with the same cancellation/disposal
pattern as C1's tug; it must prove a matched moving improvement and resource
budget before becoming a production dependency.

## CPU-only construction audit

Run `pnpm exec tsx docs/evidence/course-remaster/coast-standard/audit.mts`.
The checked-in [audit.json](audit.json) records the source SHA-256 and two
fresh-construction digests per course/detail. It verifies finite vertex/UV/
color data, actual placement matrices, manufactured map bytes, a connected
shore-contact ribbon, and once-only geometry/map retirement. No WebGL frame
or physics replay is implied by this result.

| Course | High candidate triangles (mesh + placements) | Low candidate triangles | High/low new maps | Landmark count |
| --- | ---: | ---: | ---: | ---: |
| C1 | 21,104 | 20,048 | 3.99 / 1.00 MiB | 5 |
| C2 | 17,148 | 16,260 | 3.99 / 1.00 MiB | 3 |
| C3 | 20,128 | 19,420 | 3.99 / 1.00 MiB | 4 |

These are full-course *candidate* triangles before frustum/chunk culling,
legacy-family removal and the rest of the world. They are not whole-frame
measurements. The source is 25 KiB unminified and 8 KiB gzipped as text;
only a real production bundle can establish its actual contribution to the
700 KiB player JavaScript gate. The low tier currently saves much more map
memory than geometry; phone captures may require a stronger model LOD.

## Review gates before production integration

1. Freeze a source-stamped normal baseline and capture matched full C1, C2,
   C3 Rookie rides plus C3 Pro, brake/Pier-2/breach faults and retries at
   852×393 landscape. Compare decoded moving frames, not posed stills.
2. Integrate C1 only behind a local switch, including the sky-only plate
   change. Judge the entire ride for vessel scale, quay continuity, water
   contact, landmark progression and the brake/landing camera. Reject if a
   single pretty harbor frame leaves the rest repetitive.
3. Keep collider files and physics arithmetic untouched; exact Node and two
   fresh normal-browser input replays must retain ticks, finish time and
   replay hash. Check hazard visibility and camera occlusion at both C1
   faults/retries before propagating the kit.
4. Measure loaded-track/obstacle, whole-frame draw calls/triangles, resident
   texture bytes, p50/p95 frame time, boot memory and load on physical
   landscape iPhone and Android. Existing hard limits remain 20/80k for
   track+obstacles and 300/500k/96 MB whole-frame. The player JavaScript
   allowance is 700 KiB. Source-only estimates are not a device pass.
5. Apply the accepted C1 material and water standard to C2/C3, then tune
   their distinct ship/crane/shore reads. Preserve the exact C2 landing
   connection and C3 breach geometry. Obtain uncoached phone judgments about
   the brake, lift/coast and rear-wheel landing before signing off any course.

This is the Coast component of the active
[twelve-course plan](../../../plans/sol-6.1-2026-09-29-TWELVE_COURSE_REMASTER.md).

## Parent full-ride review — first candidate rejected

The [paired full film](full-rejected-compare.mp4) puts the original on the left and the rejected C1 candidate on the right. Both use the same actual input at 852×392, low tier, Metal; finish30.35s/tail hash`6e6f8b09a5b83061`, deck-fault hash`1b27e28eb116e6f5` and all camera checks agree. [Rejection and exact source fingerprints](rejection.json) distinguish the shared candidate bytes from HEAD.

The parent reviewed chronological decoded motion from the full films, not a posed showcase. Water/quay contact and the open hazard sightline are useful, but most of the ride loses the working-harbor character: vast empty ocean, shallow generic freight/warehouse shapes and a white tiled foreground. This does **not** meet the complete visual-remaster bar. No C2/C3 rollout or course credit. The next iteration uses a detailed authored Blender harbor family, purposeful near/mid/far composition and wet shoreline material refinement; the full played comparison must pass before propagation. Raw films stay local/ignored; the paired film and per-film source/camera metadata remain evidence.

The parent-only rejected hook is preserved in [the standalone experiment](../../../../prototypes/coast-standard-v1/README.md); the production source is restored.
