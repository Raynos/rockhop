# ROCKHOP C island — production world selector

**Selected target:** the user's [C island screenshot](../../../docs/evidence/world-map-c/orbit-round4/selected-reference.jpg), with 12 roadside rally-flag towers. The [C nine-view board](mockups/map-styles/C/board-3x3.jpg) explores camera mood; the user's selected screenshot controls the island layout and visual style. The [current played selector](../../../docs/evidence/world-map-c/orbit-round4/README.md) proves rotation and 12 selections but is still a visual and performance prototype.

## Read at a glance

From the default landscape overview, the player sees one continuous, fully modeled island above turquoise water. The route begins at the working coast, enters a dense green forest and alpine foothills, crosses a warm rust quarry, and ends in white snow and high rock. A cream-colored road connects all 12 stops in that order. Each stop is a physical tower beside the road with a number plate, lamp and small red rally flag. A selected tower is clear without turning the island into a flat icon grid. There are no circular level arenas or floating domino markers.

The selected image's strengths are the legible silhouette, strong biome contrast, long 12-stop sweep, cliffs above water, and small but identifiable harbor/crane, lodge, quarry bridge and snow village. The production scene must preserve those relationships while adding model, material and lighting detail visible during a full orbit. A painted map on a plane, a single blended image, or a sharp front view that falls apart behind the island fails this spec.

## Asset and camera work

- Build the terrain as actual cliffs, ridges, cuttings, road beds, shoreline and water, with coherent back and side faces. Give the coast harbor and crane physical structure; vary tree size, trunk, canopy and clearings through the forest; make the quarry's strata, rocks and bridge read as a worked site; give the snow peaks, pines and buildings distinct forms. Keep material detail controlled so the route and flags remain readable at phone size.
- Keep the 12-stop route and current coast → alpine → quarry → snow progression. Road edges, switchbacks and bridges remain visible at overview and close zoom. Place exactly one 3D tower per course, 01–12, in route order and outside the road's riding line. Attach the real course ID, title, medal and lock state to that tower from the existing saved campaign state.
- Support a full horizontal orbit plus bounded tilt and zoom. Start at the selected reference's three-quarter overview. The camera never clips through terrain or hides a stop irretrievably; a return-to-route control restores the overview. Frame the island and selected tower at supported landscape phone widths without covering them with title, progress or Ride UI.
- Distinguish a tap from a drag. Touch, mouse and keyboard/gamepad focus must reach every tower. Keep selection targets at least 44 points even when the visible tower is smaller. Locked stops explain their prerequisite; an unlocked selection leads through the existing Ride action to the correct course. Portrait shows the rotate prompt from first paint and does not expose an unplayable map.

## Review and promotion gate

1. Record a silent *played* 360° orbit with real drag input, plus all 12 tower selections and Ride navigation at phone-landscape size. Save front, three-quarter and reverse frames from that same capture. Judge both close detail and whole-island composition against the selected screenshot; a single posed hero angle is insufficient.
2. Verify selection order, unlock state, saved medals, touch hit targets, gesture separation, camera bounds and return-to-route behavior on the real selector. Reopen from a saved career and check the state again. Preserve the current deterministic course/replay paths.
3. Measure on a physical landscape iPhone: frame times, sustained FPS, draw calls, triangles, texture/geometry memory, startup and scene switching. The scene must satisfy the game's [60 fps phone goal](../../../docs/mission.md) on its chosen device tier without making warm cached boot or first Garage use slower. Use LOD, instancing and texture discipline where measurements point, while retaining the selected reference's density.
4. Only then replace the production painted selector and remove the development-only `?map3d=1` dependency. Run the release-shell cold boot → map → C1 ride → crash → instant restart gate, plus a later course and both bikes, on the same candidate source.

The next art round should start with a front/reverse side-by-side and a short list of the three largest gaps against the selected image. The latest [forest/light pass](../../../docs/evidence/world-map-c/orbit-round4/README.md) still reports 293–297 draws, roughly 449,000 triangles and 4–5 fps on DPR2 headless SwiftShader; that is a software-renderer observation, not an iPhone verdict.
