# D3 Pro ore-cart landing lesson: played qualification

Root owns the normal HUD change; this folder freezes and compares it without
editing shared source. The baseline HUD is exactly git `4623e834:src/ui/hud.ts`.
All other application source, physics, tracks, inputs and public banks are the
same captured working-tree bytes in both builds. HEAD is `02f52c18`; this is
not a clean archive of that commit. `snapshot-manifest.json` records the full
inventory and dirty tree. Current source graph SHA is
`7bf24e94272fd37bb083f10d937762ae053e105be39272f8cbb6cd16638dd1e5`;
public inventory SHA is
`e04f5a22fefd7ac23d8586a49a2fe10211d0db8c4b0b98c1a2c5f5d03a5e7320`.

## Played windows and exact outcomes

Before left / after right:

- `review/d3-pro-cart-compare.mp4`: current clean Pro input, ticks 940–1380,
  74 frames / 3.7 s, matched endpoint `a15e326a2dce7922`.
- `review/d3-pro-fault-compare.mp4`: held GO through first ore-cart landing
  fault, then neutral input through automatic checkpoint retry and resumed GO,
  ticks 1000–1662, 111 frames / 5.55 s, matched endpoint `7bbbd108d9d1171b`.

Both cameras pass every captured frame (74/74 and 111/111), with unchanged
physics/camera outcome. Silent headless Metal, low 852×392 landscape. The cue
starts at x100, before the real x109.8 cart, persists through flight and clears
at x144 after the clean landing. On fault/retry it returns at the checkpoint.
These are recorded inputs; no fresh-player understanding is inferred.

The current complete Pro reference also matches frozen Node and production
browser: **32.458333333 s, zero faults, hash `774c599b55917f5a`**, finished.
`review/full-replay.json` retains the actual states and source identity. This
was a replay endpoint check without two unnecessary complete films.

## One text correction

Initial `RELEASE GO · LEVEL THE LANDING` overflows the fixed cue panel at the
phone viewport. `review-initial/` preserves those rejected moving pairs. Root
shortened the normal action to **RELEASE GO · LAND LEVEL**; the full accessibility
instruction remains. The identical literal correction is the only extra private
after override. The final played cue fits inside the panel without covering the
bike/contact line. Parent owns moving acceptance, not this builder.

Baseline/final player gzip: **716369→716454 B**, +85 B, **346 B spare** below the
unchanged 716800 B cap. Both frozen source graphs typecheck with zero diagnostics;
scoped prototype lint and existing Vite build gates pass. Generated catalog and
public bank are identical between phases. No physics/track/model/camera edit.
No sustained-device performance claim is made from concurrent headless capture.

## Existing recipe and limits

The existing S1/Alpine immutable snapshot/build/capture/pair scripts are reused
with D3 input and HUD override configuration. `out/` is ignored. Before privately
loads the immutable old HUD blob; after loads the corrected current HUD. The
source patch is old→new. Captures are opt-in under the parent-owned GPU lane.

The first additional before full-replay helper called the wrapper's nonexistent
`newPage()` after its cart film completed. Its browser closed in finally. The
helper was fixed to the existing `.page` API; actual current full replay succeeds.
The before window remains valid and exact. This harness mistake is not a game
failure and does not support a new regression claim.

Human Pro learning, attempts-to-clear, earned Scrap pacing and physical-phone
qualification remain open. A cue alone is not a finished course or calibrated
medal curve. All capture, browser/server and encoding work is stopped.
