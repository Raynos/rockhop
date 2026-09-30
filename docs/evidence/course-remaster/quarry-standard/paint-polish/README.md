# Quarry tread paint, one bounded final comparison

**Parent decision: retain this narrow surface polish.** D1–D3 moving sheets show a clearly smoother, warmer packed tread in the rider's near field, without changing the ledge tops, old machinery silhouettes, metal belts and bridge, warning poles or bike path. This is a shared material/painter improvement, not whole-course art acceptance. The earlier full and compact authored machinery swaps remain rejected for model grounding and silhouette regression; the ground vertex-tint candidate was too subtle.

The reproducible source change is [`quarry-paint-polish.patch`](../../../../../prototypes/quarry-authored-integration-v1/quarry-paint-polish.patch). It uses the same quarry top canvas map at lower speckle contrast and reuses the concrete normal map at `normalScale = 0.24`. The one generic `normalScaleOverride` flag in `MaterialLibrary.copyMaps` prevents the post-first-frame texture binding from resetting this specific derived material to the base `1.0` scale. No new models, maps or texture dimensions are added. Existing albedo pixels intentionally change; geometry, collision, route and RNG stay identical. The retained patch uses zero context; apply with `git apply --unidiff-zero` against its matching source.

## Frozen comparison

- Source baseline `f2f737c1cc9e68ff5b11719cf3828d30ca5ade25`; same private model bank and catalog SHA-256 `46eda21166b14a7203b6ae0e6b0ed66bf25868d9f70a95faf2fed86bf0b8537f` in both builds.
- Baseline entry SHA-256 `8a5ab01654940363d9e08aa15c048c9db7f853456049d374b902ec040bb8ce0b`; painted entry `e146a0bdcc2fb6aa813839db47310ec6f084373ae6eca29632d8165c77fcb7e6`.
- Player JS: baseline **714,679 B**, painted **714,747 B**, both pass the unchanged **716,800 B** cap. Painted `tsc --noEmit` passed after copying the repo's unrelated alpine test fixture into the private snapshot.
- `quarry-paint-polish.patch` SHA-256 `168063abc531fa4a09065c1ed80b3128070051c9cfc02a5734340110306499b2`.
- Private builds: `/private/tmp/rockhop-quarry-d1-pair-v6/before` and `/private/tmp/rockhop-quarry-paint-v1`. The latter was made from the former and changes only `zoneDeck.ts` and `library.ts` in production source. Both captures used the same input, 852×392 low landscape tier, SwiftShader renderer and deterministic camera gate.

| Ride | Baseline / paint frames | Matched final hash | Finish | Camera |
| --- | ---: | --- | ---: | --- |
| D1 Rookie full | 271 / 271 at 10 fps | `28fbe9bf33ed372e` | 27.058333 s | Pass both |
| D1 Rookie fault | 48 / 48 at 20 fps | `6128ed539a29390b` | Crash | Pass both |
| D2 Rookie full | 223 / 223 at 6 fps | `a99c0e0a6327d0c6` | 37.158333 s | Pass both |
| D3 Pro upper | 195 / 195 at 6 fps | `537a03b13cbaeb3f` | 32.458333 s | Pass both |

`replays.json` records input and exact clip/sheet hashes. The eight committed contact sheets show the same moving-camera moments before and after; full encoded clips and capture reports remain at `/private/tmp/rockhop-quarry-compact-v1/qa/{before,paint}/{full,fault,d2-full,d3-upper}/`. The visible change is large enough to judge in D1–D3 played motion; whole-course backgrounds, models and hazard design still need broader remaster work. This is not a Metal/phone performance qualification and the private 2026-09-30 baseline requires integration against current main before release.

## Normal integration

Parent decoded consecutive frames from the full played sequence and retained calmer near-field tread; the repeated box silhouettes and plate remain. Paired full/fault films and capture reports are now retained here; `paired-clip-hashes.json` identifies them. The normal player hook uses this painter for D1–D3. The late-map lifecycle test passes with real map generation at reduced painter dimensions, preserving the override and authored albedo while the ordinary derived control follows the base. App typecheck and scoped lint pass; a fresh combined A1/Snow/Quarry production build passes **715,206 B / 698.44 KiB**, unchanged cap. This build occurred while other authoring lanes were active and is not a timing qualification.

The source patch was reformatted to zero context for the whitespace gate; the original captured patch SHA-256 was `168063abc531fa4a09065c1ed80b3128070051c9cfc02a5734340110306499b2`, and the retained patch SHA-256 is `df79b7aac83db132e9b1eaadeb0ddc266ce95b3503ab44d70fa89fc4ae524d9e`. No player bytes changed in that formatting. Physical phone/readability and fresh-player course signoff stay open.
