# Bike remaster candidate evidence

**Current art candidate is v5:** see [V5.md](V5.md) and `manifest-v5.json`; [V4.md](V4.md) remains the sampling/mechanical fallback. The table below records frozen v1 geometry delivery; its dense atlas failed actual low-tier review and is superseded.

2026-09-30, built now for the requested future comparison. Parent-owned Garage integration and judgment are separate from these Blender candidate checks.

| Candidate | Triangles | Draws | Bytes | Original bytes |
|---|---:|---:|---:|---:|
| Rookie full | 32,460 | 23 | 1,103,308 | 2,283,036 |
| Pro full | 32,460 | 23 | 1,099,240 | 2,270,540 |
| Rookie LOD | 5,769 | 23 | 485,604 | 870,436 |
| Pro LOD | 5,769 | 23 | 483,936 | 864,844 |

All four pass `assets/blender/verify_hero_art.mjs` against current production counterparts. All 23 mechanical parts and 22 markers survive with identical parents/extras; local TRS worst difference is 5.96e-8. Chain/hose/spoke/blur position/topology checks have zero protected error. Both LODs additionally pass against production **full** source, recorded in `*-lod-against-full.verify.json`. Full embedded texture bytes fall from approximately 1.70 MB to .54 MB; maximum texture dimension falls from 2048 to 1024. Image dimensions imply 38,608,896 → 7,151,616 decoded RGBA bytes for full, and 10,297,344 → 2,433,024 for LOD, excluding mipmaps and driver duplication. This is a static image estimate; live GPU memory/frame pacing is unmeasured here.

The silent `baseline-rookie-orbit.mp4`, `candidate-rookie-orbit.mp4` and `candidate-pro-orbit.mp4` plus `candidate-rookie-lod-orbit.mp4` use one lighting/camera orbit recipe. They show actual exported geometry through all angles. `baseline.png` and candidate detail stills are supplementary; the clips are the review artifact. Blender orbit footage is not actual Garage footage or proof of mechanical behavior in play.

Exact source/output/master/recipe hashes, per-part triangle counts and original/candidate texture statistics live in `manifest.json`. Rebuild recipe and editable-master policy: `assets/blender/hero-remaster/bike/README.md`.

New panels/engine/exhaust and material surfaces are authored procedurally in Blender for this round. Thin rigid mechanisms reuse cleared current production geometry. No generated Hunyuan/TRELLIS geometry or UniMate animation appears in these bike exports. No public asset/catalog, physical simulation or release deployment was changed by this builder.
