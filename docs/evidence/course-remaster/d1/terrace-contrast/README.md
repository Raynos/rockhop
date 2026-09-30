# D1 Dust Devil — terrace contact contrast trial

2026-09-29. **Rejected. No game source from this trial remains.** At the actual landscape phone viewport, the four 0.4 m terrace rises still read mainly through chevron witnesses, not through distinct rock contacts. The blind baseline remains eight attempts, with five of seven failed attempts at the x≈98–104 m steps. This trial did not collect a new uncoached rider.

## Played evidence

The [baseline terrace clip](../terrace-sightline/before/terraces/clip.mp4) and [final faceted trial](after-facets/terraces/clip.mp4) replay the same Rookie recording at 852×392, 20 fps, ticks 700–1180. The [moving side-by-side](terrace-facets-comparison.mp4) places baseline on the left. Both clips have 81 frames, pass the camera box with zero riding violations, and end at the exact state hash `bd1f2fa24eb0e92a`. The moving comparison shows the fractured face remains too small at phone size to clarify the contact rise before arrival.

Two earlier versions document the boundary: [tread shading only](terrace-comparison.mp4) made a mild ochre shelf, and [tread plus uniform face tint](terrace-v2-comparison.mp4) read as a flat painted retaining wall. Each pair replays to the same `bd1f2fa24eb0e92a` hash and passes the camera check. The final variant kept the true collider ribbon, toned the tread more neutrally, and added small rock facets below the top and outside the tire line. It still failed the moving read.

The prior [full Rookie baseline](../strata-composition/phone/after/full/clip.mp4) and [blind fault/retry](../strata-composition/phone/after/fault-retry/clip.mp4) remain available. New full rides and fault clips were not retained for this rejected art trial because the phone-size moving terrace comparison already rejected the candidate.

## Scope and next design target

Trial changes touched only D1's four real ledge ribbons at x91.4, 98.4, 104.4 and 110.4 m, and the existing decorative edge geometry under those ledges. No collider, input, camera or physics change was retained. The final trial build used 673,080 B player JS gzip against the 676,864 B cap, 504 B above the 672,576 B baseline; `pnpm typecheck`, focused lint and build passed. The restored working source has no diff.

A useful next round needs a larger authored quarry cut and lighting composition at tire scale. The four real step tops must be distinguishable from the pale ground while the rider approaches at speed, with no extra apparent riding shelf. Capture a matched phone-size moving comparison and run a fresh uncoached rider before accepting an attempts-to-clear claim.
