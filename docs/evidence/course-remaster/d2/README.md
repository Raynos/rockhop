# D2 Conveyor: machinery silhouette round

Source base: `846a2c4e`. Final `src/render/world/obstacles.ts` SHA-256: `d1f469be1b95fed07d8ee043225b8c97df4752d96c54fcce134546a1a1d8dedb`. Only D2's obstacle presentation changed; compiled colliders, track and physics did not.

- [Frozen full ride before](../baseline-clips/d2-conveyor/clip.mp4) (same Rookie recording, 852×394). In motion the pulley is a black disk, its belt nearly black, and the ore-cart nose a dark wedge.
- [Head-pulley played excerpt](head-pulley-first-pass.mp4), 852×392 at 20 fps, 18–24 s of the exact Rookie recording. This is the first D2 source revision: a rotating spoke/hub face, belt cleats and stringers, plus axle supports. It precedes the cart-side and final cleat-height tweak.
- [Final cart played excerpt](after-cart-final.mp4), [frame board](cart-sheet.jpg), [capture report](cart-capture.json), 852×392 at 20 fps, 30–33.35 s of the exact same recording. The near rust tub edge, ochre rim, far wall, headgate, cut-stone load and wheel hubs read as a rail cart on the ramp rather than an unbroken mound. Camera riding box and roll violations: zero in this excerpt.

The final cart-window browser replay and Node replay match exactly at tick 4002: `3e2dd889b9e94bce`; the full Node replay finishes at 37.158 s with zero faults and original finish hash `0783873ba9ba4df4`. Pre-round full D2 obstacle cost **1,524 triangles / 9 draw calls**; final **4,164 triangles / 7 draw calls** (same compiled track, material library, and obstacle builder; painted canvas stubbed for Node measurement). The two pulleys remain one animated mesh each. Typecheck, `oxlint src/render/world/obstacles.ts`, and production Vite build pass.

The blind Pro recording faulted at x54.85–72.60 m near the feed belt four times and once at x446.62 m beyond the cart run; blind Rookie faulted at x61.23 m and x392.26 m. This visual round did not test whether a fresh rider now recognizes those faults. The dark ridden track ribbon still dominates the conveyor and cart top; that separate surface/lighting pass and physical landscape-phone pacing remain open. This is one bounded model/readability round, not a complete D2 remaster.
